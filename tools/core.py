import json
import re

from langchain_core.messages import SystemMessage, HumanMessage

from tools.tools import extract_and_exec, list_files, read_file, retrieve, retrieve_by_article

def parse_all_tool_calls(text: str) -> list[tuple]:
    """
    Parse all <tool>...</tool><input>...</input> pairs from text.
    Returns a list of (tool_name, input_dict).
    """
    pattern = r"<tool>(.*?)</tool>\s*<input>(.*?)</input>"
    matches = re.findall(pattern, text, re.DOTALL)
    pairs = []
    for tool_name, input_str in matches:
        try:
            input_dict = json.loads(input_str.strip())
            pairs.append((tool_name.strip(), input_dict))
        except json.JSONDecodeError:
            continue
    return pairs

def _auto_summary(context_text: str, max_length: int = 3000) -> str:
    """Mechanically truncate text if too long."""
    if len(context_text) <= max_length:
        return context_text
    head = context_text[:2000]
    tail = context_text[-1000:]
    hidden = len(context_text) - 3000
    return f"{head}\n\n... [{hidden} characters hidden] ...\n\n{tail}"

def _llm_summary(llm, context_text: str, max_length: int = 3000) -> str:
    """Summarize context using the LLM."""
    prompt = (
        "Summarise the following legal search results into key facts. "
        "Keep all names, dates, amounts, article numbers, and legal sources. "
        "Output plain text bullet points.\n\n"
        f"{context_text[-15000:]}\n\nKey Facts Summary:"
    )
    try:
        summary = llm.invoke(prompt, max_new_tokens=1024)
        return summary[:max_length]
    except Exception:
        return _auto_summary(context_text, max_length)

def _trim_messages(messages: list, max_chars: int):
    """
    Trim message list so total characters ≤ max_chars,
    removing oldest assistant + tool_response pairs first.
    """
    total = sum(len(m["content"]) for m in messages)
    while total > max_chars and len(messages) > 3:
        removed = False
        for idx in range(2, len(messages)):
            if messages[idx]["role"] == "user" and "<tool_response>" in messages[idx]["content"]:
                if idx > 0 and messages[idx - 1]["role"] == "assistant":
                    tool_msg = messages.pop(idx)
                    total -= len(tool_msg["content"])
                    asst_msg = messages.pop(idx - 1)
                    total -= len(asst_msg["content"])
                else:
                    tool_msg = messages.pop(idx)
                    total -= len(tool_msg["content"])
                removed = True
                break
        if not removed:
            if len(messages) > 2:
                old = messages.pop(2)
                total -= len(old["content"])
            else:
                break

def run_agent(
    system: SystemMessage,
    human: HumanMessage,
    llm,
    max_iter: int = 5,
    tools_item: str = None,
    max_new_tokens: int = None,
    max_context_chars: int = 40000,
    memory_trigger_chars: int = 15000,
):
    """
    Run an agentic loop with tool-calling for up to `max_iter` iterations.
    Returns the final LLM response string.
    """
    seen_queries = set()
    tools_item = tools_item or ""

    # Initialize message list
    messages = [
        {"role": "system", "content": system.content + "\n\n" + tools_item},
        {"role": "user", "content": human.content},
    ]

    memory = ""
    raw_context = ""

    for i in range(max_iter):
        is_last = (i == max_iter - 1)

        # Insert memory as a system message (only once)
        if memory and not any("MEMORY" in m.get("content", "") for m in messages if m["role"] == "system"):
            messages.insert(1, {"role": "system", "content": f"[MEMORY]\n{memory}"})

        # Add iteration instruction
        is_penultimate = (i == max_iter - 2)
        iter_text = f"iter count {i+1}/{max_iter}"
        if is_penultimate:
            iter_text += "  ← NEXT ITERATION IS YOUR LAST. Wrap up tool calls. Prepare your JSON output."
        if is_last:
            iter_text += "  ← FINAL ITERATION: output your JSON answer NOW. NO tool calls. Output ONLY the JSON object."
        messages.append({"role": "user", "content": iter_text})

        # Call LLM
        response = llm.invoke(messages, max_new_tokens)
        print(f"[iter {i+1}/{max_iter}] {response}\n")   # Keep: live progress

        # Save assistant response
        messages.append({"role": "assistant", "content": response})

        tool_calls = parse_all_tool_calls(response)

        if not tool_calls:
            return response

        if is_last:
            # Force return last JSON if still making tool calls
            json_match = re.search(r'(\{[\s\S]*\})', response)
            if json_match:
                return json_match.group(1)
            clean = re.split(r"<tool>", response)[0].strip()
            return clean if clean else response

        # Execute tool calls
        tool_results_parts = []
        for tool_name, tool_input in tool_calls:
            if tool_name in ("retrieve", "retrieve_by_article"):
                q = str(tool_input)
                if q in seen_queries:
                    tool_results_parts.append(f"[ALREADY RETRIEVED: {q}]")
                    continue
                seen_queries.add(q)

            try:
                if tool_name == "retrieve":
                    result = retrieve(**tool_input)
                elif tool_name == "retrieve_by_article":
                    result = retrieve_by_article(**tool_input)
                elif tool_name == "list_files":
                    result = list_files(**tool_input)
                elif tool_name == "read_file":
                    result = read_file(**tool_input)
                elif tool_name == "code":
                    result = extract_and_exec(response, tool_input.get("file_path"))
                else:
                    continue
                result_str = f"Query: {tool_input}\nResults: {json.dumps(result, indent=2)}"
            except Exception as e:
                result_str = f"[TOOL ERROR] {tool_name}: {e}"

            tool_results_parts.append(result_str)
            print(f"\n{result_str}")   # Keep: shows tool outputs

        combined = "\n\n".join(tool_results_parts)
        raw_context += combined

        messages.append({"role": "user", "content": f"<tool_response>\n{combined}\n</tool_response>"})

        # Update memory when raw context grows large
        if len(raw_context) > memory_trigger_chars:
            memory = _llm_summary(llm, raw_context)
            raw_context = ""
        else:
            memory = raw_context

        _trim_messages(messages, max_context_chars)

    return response