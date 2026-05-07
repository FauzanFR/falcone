import gc
import json
import os
import re

def _safe_gc():
    """Force garbage collection and free GPU memory if available."""
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            _safe_gc()
    except Exception:
        pass

def _gpu_mem_str() -> str:
    """Return a human-readable GPU memory usage string, or N/A."""
    try:
        import torch
        if torch.cuda.is_available():
            return f"{torch.cuda.memory_allocated(0)/1e9:.2f} GB"
    except Exception:
        pass
    return "N/A (no CUDA)"

from graph.state import FalconeState
from graph.prompts import ADVOCATUS_PROMPT, ARCHIVIST_PROMPT, CHRONOLOGIST_PROMPT, IL_CAPO_CHAT_PROMPT, IL_CAPO_COMPILE_PROMPT, IL_CAPO_ROUTE_PROMPT, LEGALIST_PROMPT
from tools.core import run_agent
from tools.one_time_call import get_llm
from tools.prompts_tools import tools
from tools.tools import parse_json_safe, read_file
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
load_dotenv()

llm = get_llm(os.getenv("LLM_BACKEND", "deepseek"))


# ---------------------------------------------------------------------------
# Graph nodes
# ---------------------------------------------------------------------------

def node_il_capo_route(state: FalconeState) -> FalconeState:
    """
    Il Capo as router: decides whether the query needs a full investigation
    or can be answered directly (chat mode).
    """
    has_file = bool(state.get("file_path"))
    cache = state.get("cached_investigation", {})
    has_cache = bool(cache)
    user_msg = f"User query: {state['query']}\nFile provided: {has_file}\nHas previous investigation cache: {has_cache}\n\nOutput routing JSON only."

    response = llm.invoke([
        {"role": "system", "content": IL_CAPO_ROUTE_PROMPT},
        {"role": "user", "content": user_msg}
    ], max_new_tokens=512)

    routing = parse_json_safe(response, {
        "mode": "investigate" if has_file else "chat",
        "reasoning": "fallback",
        "pipeline": ["Archivist", "Chronologist", "Legalist", "Advocatus"],
        "query_en": state["query"],
        "case_context": "unknown"
    })

    # If a file is present and no cache exists, force investigation mode
    if has_file and not has_cache:
        routing["mode"] = "investigate"

    print(f"[Il Capo Route] mode={routing.get('mode')} | cache={has_cache} | {routing.get('case_context', '')}")

    return {
        "routing": routing,
        "messages": [f"[Il Capo] {routing.get('case_context', 'Routing complete')}"]
    }


def node_archivist(state: FalconeState) -> FalconeState:
    """
    Archivist: extracts facts from uploaded documents.
    """
    _safe_gc()
    print(f"[Archivist] Starting... GPU: {_gpu_mem_str()}")

    merged = run_agent(
        system=SystemMessage(content=ARCHIVIST_PROMPT),
        human=HumanMessage(content=f"path file :{state['file_path']}"),
        llm=llm,
        max_iter=5,
        tools_item=tools(False, False, False, True, True),
        max_new_tokens=2048 * 4
    )
    print(f"[Archivist] Done!")

    fallback = {"entities": [], "events": [], "obligations": [], "cross_references": [], "source_articles": []}
    parsed = parse_json_safe(merged, fallback)

    # Rescue parse when output is not valid JSON
    if parsed == fallback and len(merged) > 100:
        print("[Archivist] Output is not valid JSON, performing rescue parse...")
        rescue_response = llm.invoke(
            [
                {"role": "system", "content": "Convert the following text into the required JSON format with entities, events, obligations, cross_references. Output ONLY JSON."},
                {"role": "user", "content": merged[:20000]}
            ],
            max_new_tokens=2048
        )
        parsed = parse_json_safe(rescue_response, fallback)

    return {
        "archivist_facts": parsed,
        "messages": [f"[Archivist] Extracted facts"]
    }


def node_chronologist(state: FalconeState) -> FalconeState:
    """
    Chronologist: builds a timeline from the facts found by Archivist.
    """
    _safe_gc()
    print(f"[Chronologist] Starting...")

    response = llm.invoke(
        [
            {"role": "system", "content": CHRONOLOGIST_PROMPT},
            {"role": "user", "content": f"Build timeline from facts. Output JSON only.\n\n{json.dumps(state['archivist_facts'], indent=2)}"}
        ],
        max_new_tokens=3000
    )

    fallback_chron = {"timeline": [], "gaps": [], "anomalies": [], "patterns": []}
    output = parse_json_safe(response, fallback_chron)

    # Rescue for missing timeline
    if not output.get("timeline") and len(response) > 100:
        print("[Chronologist] Output is not valid JSON, performing rescue parse...")
        rescue_response = llm.invoke([
            {"role": "system", "content": "Convert the following timeline analysis into JSON with keys: timeline (list of {date, event}), gaps (list), anomalies (list), patterns (list). Output ONLY JSON."},
            {"role": "user", "content": response[:15000]}
        ], max_new_tokens=2048)
        output = parse_json_safe(rescue_response, fallback_chron)

    print(f"[Chronologist] Timeline: {len(output.get('timeline', []))} events")

    return {
        "chronologist_output": output,
        "messages": [f"[Chronologist] Timeline built with {len(output.get('timeline', []))} events"]
    }


def node_legalist(state: FalconeState) -> FalconeState:
    """
    Legalist: uses facts & timeline to retrieve and assess legal violations.
    """
    _safe_gc()
    print(f"[Legalist] Starting agentic retrieval...")

    tools_item = tools(retrieve=True, retrieve_by_article=True)

    context = f"""
FACTS FROM ARCHIVIST:
{json.dumps(state['archivist_facts'], indent=2)}

TIMELINE FROM CHRONOLOGIST:
{json.dumps(state['chronologist_output'], indent=2)}
"""

    response = run_agent(
        system=SystemMessage(content=LEGALIST_PROMPT + """
\nMANDATORY: Before outputting any JSON, you MUST call the retrieve tool
at least 3 times with different queries based on the facts provided.
Do NOT output violations JSON until you have retrieved relevant articles.
"""),
        human=HumanMessage(content=context),
        llm=llm,
        max_iter=8,
        tools_item=tools_item,
        max_new_tokens=2048 * 2
    )

    fallback_leg = {"violations": [], "legal_gaps": [], "applicable_frameworks": []}
    output = parse_json_safe(response, fallback_leg) or fallback_leg

    if not output.get("violations") and len(response) > 100:
        print("[Legalist] Output is not valid JSON, performing rescue parse...")
        rescue_response = llm.invoke([
            {"role": "system", "content": "Convert the following legal analysis into JSON with keys: violations (list of {article, description, confidence}), legal_gaps (list), applicable_frameworks (list of strings). Output ONLY JSON."},
            {"role": "user", "content": response[:15000]}
        ], max_new_tokens=2048)
        output = parse_json_safe(rescue_response, fallback_leg) or fallback_leg

    # Print violation summary
    violations_count = len(output.get('violations', []))
    print(f"[Legalist] Found {violations_count} violations")
    for v in output.get('violations', []):
        print(f"  - {v.get('article', 'Unknown')}: confidence {v.get('confidence', 0)}")

    return {
        "legalist_output": output,
        "messages": [f"[Legalist] Violations assessed: {violations_count} found"]
    }


def node_advocatus(state: FalconeState) -> FalconeState:
    """
    Advocatus Diaboli: challenges Legalist's findings to test evidence strength.
    """
    _safe_gc()
    print(f"[Advocatus] Starting...")

    findings = state.get("legalist_rebuttal") or state["legalist_output"]
    round_num = state.get('debate_rounds', 0) + 1

    if round_num > 1:
        tools_item = tools(retrieve=True, retrieve_by_article=True)
    else:
        tools_item = tools(retrieve=True, retrieve_by_article=True, list_files=True, read_file=True)

    human_content = f"""
ROUND {round_num}

FACTS FROM ARCHIVIST:
{json.dumps(state['archivist_facts'], indent=2)[:50000]}

LEGALIST FINDINGS:
{json.dumps(findings, indent=2)[:50000]}

PREVIOUS CHALLENGES:
{json.dumps(state.get('advocatus_output', {}).get('challenges', []), indent=2) if round_num > 1 else 'None'}

path file :{state['file_path']}
"""

    response = run_agent(
        system=SystemMessage(content=ADVOCATUS_PROMPT),
        human=HumanMessage(content=human_content),
        llm=llm,
        max_iter=5,
        tools_item=tools_item,
        max_new_tokens=2048 * 3
    )

    fallback = {
        "challenges": [],
        "overall_assessment": "unknown",
        "recommendation": "investigate_further"
    }
    output = parse_json_safe(response, fallback)

    # Rescue parsing if not valid JSON
    if not output.get("challenges") and len(response) > 200:
        print("[Advocatus] Output is not valid JSON, performing rescue parse...")

        # Strategy 1: extract JSON block from markdown
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
        if json_match:
            output = parse_json_safe(json_match.group(1), fallback)

        # Strategy 2: ask LLM to convert text to JSON
        if not output.get("challenges"):
            rescue_prompt = f"""Extract challenges, overall_assessment, and recommendation from this legal analysis.
Return ONLY valid JSON. No markdown, no explanation.

Analysis text:
{response[:15000]}

Required JSON format:
{{
  "challenges": [
    {{
      "target_violation": "Article X...",
      "challenge": "...",
      "severity": "fatal | significant | minor",
      "verdict": "invalidated | weakened | upheld"
    }}
  ],
  "overall_assessment": "strong | moderate | weak",
  "recommendation": "proceed | investigate_further | insufficient_evidence"
}}

JSON:"""
            rescue_response = llm.invoke(
                [{"role": "user", "content": rescue_prompt}],
                max_new_tokens=2048 * 2
            )
            output = parse_json_safe(rescue_response, fallback)

        # Strategy 3: manual regex to extract severity/verdict
        if not output.get("challenges"):
            print("[Advocatus] Rescue juga gagal, ekstrak manual...")
            challenges = []
            lines = response.split("\n")
            current_challenge = {}
            for line in lines:
                if "**Target:**" in line or "Challenge" in line:
                    if current_challenge and "verdict" in current_challenge:
                        challenges.append(current_challenge)
                    current_challenge = {"target_violation": "", "challenge": "", "severity": "minor", "verdict": "upheld"}
                if "**Severity:**" in line:
                    sev = line.split("**Severity:**")[-1].strip().lower()
                    if "fatal" in sev:
                        current_challenge["severity"] = "fatal"
                    elif "significant" in sev:
                        current_challenge["severity"] = "significant"
                    else:
                        current_challenge["severity"] = "minor"
                if "**Verdict:**" in line:
                    ver = line.split("**Verdict:**")[-1].strip().lower()
                    if "invalidated" in ver:
                        current_challenge["verdict"] = "invalidated"
                    elif "weakened" in ver:
                        current_challenge["verdict"] = "weakened"
                    else:
                        current_challenge["verdict"] = "upheld"
            if current_challenge and "verdict" in current_challenge:
                challenges.append(current_challenge)

            if challenges:
                output["challenges"] = challenges
                fatal_count = sum(1 for c in challenges if c["verdict"] == "invalidated" and c["severity"] == "fatal")
                if fatal_count > len(challenges) / 2:
                    output["overall_assessment"] = "weak"
                elif fatal_count > 0:
                    output["overall_assessment"] = "moderate"
                else:
                    output["overall_assessment"] = "strong"

    num_challenges = len(output.get('challenges', []))
    print(f"[Advocatus] Challenges: {num_challenges}")
    if num_challenges > 0:
        for c in output["challenges"][:3]:
            print(f"  - {c.get('target_violation', '?')}: {c.get('verdict', '?')} ({c.get('severity', '?')})")
    print(f"[Advocatus] Assessment: {output.get('overall_assessment', 'unknown')}")

    return {
        "advocatus_output": output,
        "messages": [f"[Advocatus] Assessment: {output.get('overall_assessment', 'unknown')}, {num_challenges} challenges"]
    }


def node_legalist_rebuttal(state: FalconeState) -> FalconeState:
    """
    Legalist rebuts Advocatus' challenges in subsequent debate rounds.
    """
    _safe_gc()
    print(f"[Legalist Rebuttal] Round {state.get('debate_rounds', 0) + 1}")

    tools_item = tools(
        retrieve=True,
        retrieve_by_article=True,
        read_file=True,
        list_files=True
    )

    human_content = f"""
ROUND {state.get('debate_rounds', 0) + 1}

CASE FILES: {state.get('file_path', 'Not provided')}

ORIGINAL FINDINGS:
{json.dumps(state['legalist_output'], indent=2)}

ADVOCATUS CHALLENGES:
{json.dumps(state['advocatus_output'], indent=2)}

FACTS FROM ARCHIVIST:
{json.dumps(state['archivist_facts'], indent=2)}

path file :{state['file_path']}
"""

    response = run_agent(
        system=SystemMessage(content=LEGALIST_PROMPT),
        human=HumanMessage(content=human_content),
        llm=llm,
        max_iter=6,
        tools_item=tools_item,
        max_new_tokens=2048 * 2
    )

    fallback_reb = {"violations": [], "legal_gaps": [], "applicable_frameworks": []}
    output = parse_json_safe(response, fallback_reb) or fallback_reb

    if not output.get("violations") and len(response) > 100:
        print("[Legalist Rebuttal] Output bukan JSON valid, melakukan rescue parse...")
        rescue_response = llm.invoke([
            {"role": "system", "content": "Convert the following legal rebuttal into JSON with keys: violations (list of {article, description, confidence}), legal_gaps (list), applicable_frameworks (list of strings). Output ONLY JSON."},
            {"role": "user", "content": response[:15000]}
        ], max_new_tokens=2048)
        output = parse_json_safe(rescue_response, fallback_reb) or fallback_reb

    print(f"[Legalist Rebuttal] Defended {len(output.get('violations', []))} violations")

    return {
        "legalist_rebuttal": output,
        "debate_rounds": state.get("debate_rounds", 0) + 1,
        "messages": [f"[Legalist] Rebuttal round {state.get('debate_rounds', 0) + 1}"]
    }


def node_il_capo_compile(state: FalconeState) -> FalconeState:
    """
    Il Capo (compile mode): produces the final investigation report.
    """
    print(f"[Il Capo] Compiling final report...")

    entities_raw = state["archivist_facts"].get("entities", [])
    entities = [
        e["name"] if isinstance(e, dict) else str(e)
        for e in entities_raw
    ]

    violations = (state.get("legalist_rebuttal") or state["legalist_output"]).get("violations", [])
    challenges = state["advocatus_output"].get("challenges", [])

    summary = json.dumps({
        "original_query": state.get("query", ""),
        "entities": entities,
        "events": len(state["chronologist_output"].get("timeline", [])),
        "timeline": state["chronologist_output"].get("timeline", [])[:10],
        "violations": violations,
        "challenges": challenges,
    }, indent=2)

    response = llm.invoke([
        {"role": "system", "content": IL_CAPO_COMPILE_PROMPT},
        {"role": "user", "content": f"Compile final report. Address the original query directly in your conclusion.\n\n{summary}"}
    ], 2048 * 2)

    # Cache investigation for follow-up queries
    cached = {
        "query": state.get("query", ""),
        "entities": entities,
        "timeline": state["chronologist_output"].get("timeline", []),
        "violations": violations,
        "challenges": challenges,
        "overall_assessment": state["advocatus_output"].get("overall_assessment", "unknown"),
        "recommendation": state["advocatus_output"].get("recommendation", ""),
        "legal_frameworks": (state.get("legalist_rebuttal") or state["legalist_output"]).get("applicable_frameworks", []),
    }

    return {
        "final_report": response,
        "cached_investigation": cached,
        "messages": ["[Il Capo] Report compiled"]
    }


def node_il_capo_chat(state: FalconeState) -> FalconeState:
    """
    Il Capo in direct chat mode: answers queries without a full pipeline.
    """
    history = state.get("conversation_history", [])
    cache = state.get("cached_investigation", {})

    # Use last 6 messages, skip long reports
    recent = [
        m for m in history
        if not str(m.get("content", "")).startswith("__markdown__")
    ][-6:]

    human_content = ""

    if cache:
        human_content += f"""PREVIOUS INVESTIGATION SUMMARY:
Original query: {cache.get('query', 'N/A')}
Entities: {', '.join(cache.get('entities', [])[:10])}
Timeline events: {len(cache.get('timeline', []))}
Violations found: {len(cache.get('violations', []))}
Overall assessment: {cache.get('overall_assessment', 'unknown').upper()}
Recommendation: {cache.get('recommendation', 'N/A')}
Legal frameworks: {', '.join(cache.get('legal_frameworks', [])[:5])}

Violations detail:
{json.dumps(cache.get('violations', [])[:5], indent=2)}

Challenges:
{json.dumps(cache.get('challenges', [])[:5], indent=2)}

"""

    if recent:
        human_content += f"CONVERSATION HISTORY:\n{json.dumps(recent, indent=2)}\n\n"

    human_content += f"CURRENT QUERY:\n{state['query']}"

    response = run_agent(
        system=SystemMessage(content=IL_CAPO_CHAT_PROMPT),
        human=HumanMessage(content=human_content),
        llm=llm,
        max_iter=3,
        tools_item=tools(retrieve=True, retrieve_by_article=True),
        max_new_tokens=1024
    )

    return {
        "final_report": response,
        "messages": ["[Il Capo] Direct response"]
    }


# ---------------------------------------------------------------------------
# Edge decision functions
# ---------------------------------------------------------------------------

def decide_route(state: FalconeState) -> str:
    """Determine the route based on the mode in `routing`."""
    mode = state.get("routing", {}).get("mode", "investigate")
    print(f"[Il Capo Router] mode: {mode}")
    return mode


def decide_debate(state: FalconeState) -> str:
    """Decide whether to continue the debate or compile the final report."""
    rounds = state.get("debate_rounds", 0)
    challenges = state["advocatus_output"].get("challenges", [])

    # Count unresolved challenges with high severity
    unresolved = [
        c for c in challenges
        if c.get("verdict") in ["invalidated", "weakened"]
        and c.get("severity") in ["fatal", "significant"]
    ]

    print(f"[Judge] Rounds: {rounds} | Unresolved: {len(unresolved)}")

    if rounds >= 2 or len(unresolved) == 0:
        print(f"[Judge] Decision: compile")
        return "compile"

    print(f"[Judge] Decision: rebuttal")
    return "rebuttal"