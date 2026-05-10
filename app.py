import streamlit as st
import time
import json
import sys
import os

# ── Import Falcone pipeline ───────────────────────────────────────────────
_pipeline_error = None
try:
    from graph.graph import graph
    from graph.state import FalconeState
    PIPELINE_READY = True
except Exception as e:
    _pipeline_error = str(e)
    PIPELINE_READY = False
    print(_pipeline_error)

st.set_page_config(
    page_title="Falcone AI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Courier+Prime:ital,wght@0,400;0,700;1,400&family=Cinzel:wght@400;600;700&display=swap');

/* ── Reset & base ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, .stApp {
    background: #1a1610 !important;
    color: #c9b47a !important;
    font-family: 'Courier Prime', monospace !important;
}

/* Hide streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
section[data-testid="stSidebar"] { display: none; }

/* ── Layout shell ── */
.main .block-container {
    max-width: 100% !important;
    padding: 0 !important;
}

/* ── Top bar ── */
.falcone-header {
    display: flex;
    align-items: center;
    gap: 18px;
    padding: 18px 32px 14px;
    border-bottom: 1px solid #3a3020;
    background: #141210;
}
.falcone-logo {
    width: 44px;
    height: 44px;
    opacity: 0.92;
}
.falcone-title {
    font-family: 'Cinzel', serif;
    font-size: 22px;
    font-weight: 600;
    color: #d4935a;
    letter-spacing: 0.12em;
    line-height: 1;
}
.falcone-sub {
    font-size: 10px;
    color: #6b5a3a;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-top: 3px;
}
.header-badge {
    margin-left: auto;
    font-size: 10px;
    color: #4a7c59;
    background: #0f1f14;
    border: 1px solid #2a5a38;
    border-radius: 2px;
    padding: 4px 10px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
}

/* ── Main layout ── */
.falcone-body {
    display: flex;
    height: calc(100vh - 77px);
    overflow: hidden;
}

/* ── Chat pane ── */
.chat-pane {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    transition: margin-right 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ── Messages area ── */
.messages-area {
    flex: 1;
    overflow-y: auto;
    padding: 28px 36px;
    scrollbar-width: thin;
    scrollbar-color: #3a3020 transparent;
}
.messages-area::-webkit-scrollbar { width: 4px; }
.messages-area::-webkit-scrollbar-track { background: transparent; }
.messages-area::-webkit-scrollbar-thumb { background: #3a3020; border-radius: 2px; }

/* ── Message bubbles ── */
.msg-user {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 20px;
}
.msg-user .bubble {
    background: #2a2018;
    border: 1px solid #3a3020;
    border-radius: 2px 2px 2px 12px;
    padding: 12px 18px;
    max-width: 65%;
    color: #c9b47a;
    font-size: 14px;
    line-height: 1.6;
}
.msg-assistant {
    display: flex;
    gap: 12px;
    margin-bottom: 24px;
    align-items: flex-start;
}
.msg-assistant .avatar {
    width: 28px;
    height: 28px;
    flex-shrink: 0;
    margin-top: 3px;
}
.msg-assistant .bubble {
    background: #161410;
    border: 1px solid #2a2018;
    border-radius: 2px 12px 12px 2px;
    padding: 16px 20px;
    max-width: 75%;
    color: #b8a46a;
    font-size: 14px;
    line-height: 1.7;
}
.msg-assistant .bubble-md {
    background: #161410;
    border: 1px solid #2a2018;
    border-radius: 2px 12px 12px 2px;
    padding: 16px 20px;
    color: #b8a46a;
    font-size: 14px;
    line-height: 1.7;
    max-width: 75%;
}
.msg-assistant .bubble-md h1,
.msg-assistant .bubble-md h2,
.msg-assistant .bubble-md h3 {
    font-family: "Cinzel", serif;
    color: #d4935a;
    border-bottom: 1px solid #2a2018;
    padding-bottom: 6px;
    margin-bottom: 10px;
    letter-spacing: 0.08em;
}
.msg-assistant .bubble-md table {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;
    font-size: 13px;
}
.msg-assistant .bubble-md th {
    background: #1e1a12;
    color: #d4935a;
    padding: 8px 12px;
    border: 1px solid #2a2018;
    text-align: left;
}
.msg-assistant .bubble-md td {
    padding: 7px 12px;
    border: 1px solid #2a2018;
    color: #b8a46a;
}
.msg-assistant .bubble-md tr:nth-child(even) td {
    background: #0e0c08;
}
.msg-assistant .bubble-md strong {
    color: #d4935a;
}
.msg-assistant .bubble-md hr {
    border-color: #2a2018;
    margin: 12px 0;
}
.msg-assistant .bubble h3 {
    font-family: 'Cinzel', serif;
    font-size: 13px;
    color: #d4935a;
    margin-bottom: 12px;
    letter-spacing: 0.08em;
    border-bottom: 1px solid #2a2018;
    padding-bottom: 8px;
}
.msg-assistant .bubble .section-label {
    font-size: 10px;
    color: #6b5a3a;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin: 12px 0 6px;
}
.msg-assistant .bubble p { margin-bottom: 8px; }

/* ── Empty state ── */
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    gap: 16px;
    opacity: 0.5;
}
.empty-state .big-logo { width: 72px; height: 72px; }
.empty-state p {
    font-family: 'Cinzel', serif;
    font-size: 13px;
    color: #6b5a3a;
    letter-spacing: 0.2em;
    text-transform: uppercase;
}

/* ── Input bar ── */
.input-bar {
    padding: 16px 36px 20px;
    border-top: 1px solid #2a2018;
    background: #141210;
    display: flex;
    flex-direction: column;
    gap: 10px;
}
.input-row {
    display: flex;
    gap: 10px;
    align-items: flex-end;
}

/* Override streamlit input */
.stTextArea textarea {
    background: #1e1c18 !important;
    border: 1px solid #3a3020 !important;
    border-radius: 2px !important;
    color: #c9b47a !important;
    font-family: 'Courier Prime', monospace !important;
    font-size: 14px !important;
    resize: none !important;
    padding: 12px 16px !important;
}
.stTextArea textarea:focus {
    border-color: #d4935a !important;
    box-shadow: none !important;
    outline: none !important;
}
.stTextArea textarea::placeholder { color: #4a3a20 !important; }
.stTextArea label { display: none !important; }

.stFileUploader {
    background: #1e1c18 !important;
    border: 1px dashed #3a3020 !important;
    border-radius: 2px !important;
    padding: 8px 12px !important;
}
.stFileUploader label { color: #6b5a3a !important; font-size: 12px !important; }
[data-testid="stFileUploaderDropzone"] {
    background: transparent !important;
    border: none !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] { color: #4a3a20 !important; font-size: 12px !important; }

/* Submit button */
.stButton > button {
    background: #d4935a !important;
    color: #1a1610 !important;
    border: none !important;
    border-radius: 2px !important;
    font-family: 'Cinzel', serif !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    letter-spacing: 0.15em !important;
    padding: 12px 24px !important;
    cursor: pointer !important;
    transition: background 0.2s !important;
    white-space: nowrap !important;
}
.stButton > button:hover { background: #c07840 !important; }
.stButton > button:disabled { background: #3a3020 !important; color: #6b5a3a !important; }

/* ── Agent panel ── */
.agent-panel {
    width: 0;
    overflow: hidden;
    transition: width 0.35s cubic-bezier(0.4, 0, 0.2, 1);
    border-left: 0px solid #2a2018;
    background: #0f0e0c;
    display: flex;
    flex-direction: column;
}
.agent-panel.open {
    width: 380px;
    border-left-width: 1px;
}
.agent-panel-inner {
    width: 380px;
    height: 100%;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}
.agent-panel-header {
    padding: 18px 20px 14px;
    border-bottom: 1px solid #2a2018;
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
}
.agent-panel-title {
    font-family: 'Cinzel', serif;
    font-size: 11px;
    color: #6b5a3a;
    letter-spacing: 0.25em;
    text-transform: uppercase;
}
.agent-panel-close {
    margin-left: auto;
    cursor: pointer;
    color: #4a3a20;
    font-size: 16px;
    line-height: 1;
    padding: 2px 6px;
    border-radius: 2px;
    transition: color 0.2s;
}
.agent-panel-close:hover { color: #c9b47a; }
.agent-panel-body {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    scrollbar-width: thin;
    scrollbar-color: #2a2018 transparent;
}

/* ── Agent cards ── */
.agent-card {
    border: 1px solid #2a2018;
    border-radius: 2px;
    margin-bottom: 12px;
    overflow: hidden;
    transition: border-color 0.3s;
}
.agent-card.active { border-color: #d4935a; }
.agent-card.done { border-color: #2a5a38; }
.agent-card.waiting { opacity: 0.4; }

.agent-card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    background: #141210;
    cursor: pointer;
}
.agent-indicator {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    flex-shrink: 0;
}
.indicator-waiting { background: #3a3020; }
.indicator-active {
    background: #d4935a;
    animation: pulse 1.2s ease-in-out infinite;
}
.indicator-done { background: #4a7c59; }
.indicator-error { background: #7c3a3a; }

@keyframes pulse {
    0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(212,147,90,0.4); }
    50% { opacity: 0.7; box-shadow: 0 0 0 4px rgba(212,147,90,0); }
}

.agent-name {
    font-family: 'Cinzel', serif;
    font-size: 11px;
    color: #c9b47a;
    letter-spacing: 0.1em;
}
.agent-status-text {
    margin-left: auto;
    font-size: 10px;
    color: #4a3a20;
    letter-spacing: 0.1em;
}
.agent-card.active .agent-status-text { color: #d4935a; }
.agent-card.done .agent-status-text { color: #4a7c59; }

.agent-card-body {
    padding: 10px 14px 12px;
    border-top: 1px solid #1e1c18;
    background: #0f0e0c;
}
.agent-log {
    font-size: 11px;
    color: #6b5a3a;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-word;
}
.agent-log .log-key { color: #8a7a4a; }
.agent-log .log-val { color: #a09060; }
.agent-log .log-good { color: #4a7c59; }
.agent-log .log-warn { color: #d4935a; }

/* ── Thinking dots ── */
.thinking {
    display: flex;
    gap: 5px;
    padding: 4px 0;
}
.thinking span {
    width: 5px; height: 5px;
    background: #d4935a;
    border-radius: 50%;
    animation: bounce 1.4s ease-in-out infinite;
}
.thinking span:nth-child(2) { animation-delay: 0.2s; }
.thinking span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce {
    0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
    40% { transform: translateY(-5px); opacity: 1; }
}

/* ── Toggle button ── */
[data-testid="stButton"] > button[kind="secondary"] {
    background: transparent !important;
    color: #6b5a3a !important;
    border: 1px solid #3a3020 !important;
    font-size: 10px !important;
    padding: 6px 12px !important;
    letter-spacing: 0.15em !important;
    transition: all 0.2s !important;
    white-space: nowrap !important;
}
[data-testid="stButton"] > button[kind="secondary"]:hover {
    border-color: #d4935a !important;
    color: #d4935a !important;
    background: transparent !important;
}

/* ── Streamlit layout overrides ── */
[data-testid="stVerticalBlock"] > div { padding: 0 !important; gap: 0 !important; }
[data-testid="stHorizontalBlock"] { gap: 0 !important; }
div[data-testid="column"] { padding: 0 !important; }
</style>
""", unsafe_allow_html=True)

# ── SVG Logo (inline, your 4-circle mandala) ──────────────────────────────
LOGO_SVG = """<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <circle cx="50" cy="32" r="22" fill="none" stroke="#d4935a" stroke-width="2.2"/>
  <circle cx="50" cy="68" r="22" fill="none" stroke="#d4935a" stroke-width="2.2"/>
  <circle cx="32" cy="50" r="22" fill="none" stroke="#d4935a" stroke-width="2.2"/>
  <circle cx="68" cy="50" r="22" fill="none" stroke="#d4935a" stroke-width="2.2"/>
  <circle cx="50" cy="50" r="29" fill="none" stroke="#d4935a" stroke-width="1.4" opacity="0.5"/>
</svg>"""

LOGO_B64 = "data:image/svg+xml;base64," + __import__('base64').b64encode(LOGO_SVG.encode()).decode()

# ── Session state ─────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "panel_open" not in st.session_state:
    st.session_state.panel_open = False
if "agent_states" not in st.session_state:
    st.session_state.agent_states = {}
if "running" not in st.session_state:
    st.session_state.running = False
if "cached_investigation" not in st.session_state:
    st.session_state.cached_investigation = {}
if "last_file_path" not in st.session_state:
    st.session_state.last_file_path = None

AGENTS = ["Il Capo", "Archivist", "Chronologist", "Legalist", "Advocatus Diaboli"]

def init_agent_states():
    return {a: {"status": "waiting", "log": ""} for a in AGENTS}

def render_header():
    left, right = st.columns([10, 1])
    with left:
        st.markdown(f"""
        <div class="falcone-header">
            <img class="falcone-logo" src="{LOGO_B64}" alt="OOM"/>
            <div>
                <div class="falcone-title">FALCONE AI</div>
                <div class="falcone-sub">Forensic Document Intelligence · OOM</div>
            </div>
            <div class="header-badge">● SYSTEM ACTIVE</div>
        </div>
        """, unsafe_allow_html=True)
    with right:
        st.markdown('<div style="padding:14px 8px 0 0">', unsafe_allow_html=True)
        icon = "✕" if st.session_state.panel_open else "⚖"
        label = "CLOSE" if st.session_state.panel_open else "AGENTS"
        if st.button(f"{icon} {label}", key="toggle_panel", disabled=st.session_state.running):
            st.session_state.panel_open = not st.session_state.panel_open
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

def render_agent_card(name, state):
    status = state["status"]
    log = state["log"]

    css_class = {"waiting": "waiting", "active": "active", "done": "done", "error": "active"}.get(status, "waiting")
    indicator_class = f"indicator-{status}"
    status_label = {"waiting": "STANDBY", "active": "PROCESSING", "done": "COMPLETE", "error": "ERROR"}.get(status, "STANDBY")

    log_html = f'<div class="agent-log">{log}</div>' if log else ""
    if status == "active" and not log:
        log_html = '<div class="thinking"><span></span><span></span><span></span></div>'

    st.markdown(f"""
    <div class="agent-card {css_class}">
        <div class="agent-card-header">
            <div class="agent-indicator {indicator_class}"></div>
            <div class="agent-name">{name}</div>
            <div class="agent-status-text">{status_label}</div>
        </div>
        {"" if not log and status == "waiting" else f'<div class="agent-card-body">{log_html}</div>'}
    </div>
    """, unsafe_allow_html=True)

def render_messages():
    if not st.session_state.messages:
        st.markdown(f"""
        <div class="empty-state">
            <img class="big-logo" src="{LOGO_B64}" alt=""/>
            <p>Upload a case file and submit your query</p>
        </div>
        """, unsafe_allow_html=True)
        return

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="msg-user">
                <div class="bubble">{msg["content"]}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            content = msg["content"]
            if content.startswith("__markdown__"):
                md_content = content[len("__markdown__"):]
                # Avatar dulu
                st.markdown(f'''<div class="msg-assistant"><img class="avatar" src="{LOGO_B64}" alt=""/><div class="bubble-md">''', unsafe_allow_html=True)
                st.markdown(md_content)
                st.markdown('</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="msg-assistant">
                    <img class="avatar" src="{LOGO_B64}" alt=""/>
                    <div class="bubble">{content}</div>
                </div>
                """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Node → Agent name mapping
# ─────────────────────────────────────────────────────────────────────────────
NODE_TO_AGENT = {
    "il_capo_route":     "Il Capo",
    "il_capo_chat":      "Il Capo",
    "archivist":         "Archivist",
    "chronologist":      "Chronologist",
    "legalist":          "Legalist",
    "legalist_rebuttal": "Legalist",
    "advocatus":         "Advocatus Diaboli",
    "il_capo_compile":   "Il Capo",
}

def summarize_node_output(node_name: str, state: dict) -> str:
    """Bikin log singkat dari output tiap node buat ditampilin di panel."""
    try:
        if node_name == "archivist":
            facts = state.get("archivist_facts", {})
            return (
                f"→ entities: {len(facts.get('entities', []))} found\n"
                f"→ events: {len(facts.get('events', []))} extracted\n"
                f"→ obligations: {len(facts.get('obligations', []))} mapped"
            )
        elif node_name == "chronologist":
            out = state.get("chronologist_output", {})
            return (
                f"→ timeline: {len(out.get('timeline', []))} events\n"
                f"→ gaps: {len(out.get('gaps', []))} detected\n"
                f"→ anomalies: {len(out.get('anomalies', []))} flagged"
            )
        elif node_name in ("legalist", "legalist_rebuttal"):
            key = "legalist_rebuttal" if node_name == "legalist_rebuttal" else "legalist_output"
            out = state.get(key, {})
            viols = out.get("violations", [])
            fw = out.get("applicable_frameworks", [])
            label = "Rebuttal" if node_name == "legalist_rebuttal" else "Retrieval"
            return (
                f"→ {label} round {state.get('debate_rounds', 1)}\n"
                f"→ violations: {len(viols)} mapped\n"
                f"→ frameworks: {', '.join(fw[:3]) if fw else 'N/A'}"
            )
        elif node_name == "advocatus":
            out = state.get("advocatus_output", {})
            challenges = out.get("challenges", [])
            fatal = sum(1 for c in challenges if c.get("severity") == "fatal")
            sig   = sum(1 for c in challenges if c.get("severity") == "significant")
            minor = sum(1 for c in challenges if c.get("severity") == "minor")
            assessment = out.get("overall_assessment", "unknown").upper()
            return (
                f"→ challenges: {len(challenges)}\n"
                f"→ fatal: {fatal} | significant: {sig} | minor: {minor}\n"
                f"→ assessment: {assessment}"
            )
        elif node_name == "il_capo_compile":
            return "→ Final report compiled\n→ Pipeline complete"
        else:
            return "→ Done"
    except Exception:
        return "→ Done"


def format_final_report(state: dict) -> str:
    """
    Return final_report string.
    Kalau Il Capo output markdown (ada # atau |), return as-is.
    Kalau kosong, rakitin fallback dari state.
    Flag "__markdown__" prefix dipakai render_messages buat pilih renderer.
    """
    raw = state.get("final_report", "")

    if raw and len(raw.strip()) > 50:
        # Selalu render sebagai markdown — st.markdown() handle semua format
        return "__markdown__" + raw.strip()

    # Fallback: rakitin dari state
    violations = (state.get("legalist_rebuttal") or state.get("legalist_output", {})).get("violations", [])
    advocatus  = state.get("advocatus_output", {})
    challenges = advocatus.get("challenges", [])
    assessment     = advocatus.get("overall_assessment", "unknown").upper()
    recommendation = advocatus.get("recommendation", "investigate_further").replace("_", " ").upper()
    fatal_count = sum(1 for c in challenges if c.get("severity") == "fatal")
    sig_count   = sum(1 for c in challenges if c.get("severity") == "significant")
    viols_html = "<br/>".join(
        f"· {v.get('article', 'Unknown')} · Confidence: {v.get('confidence', '?')}"
        for v in violations[:5]
    ) or "No violations mapped."

    return f"""__markdown__## INVESTIGATION REPORT — PARMALAT FINANCIAL FRAUD (1995–2003)

**Case:** Systematic falsification of financial statements, fabrication of offshore assets, and defrauding of international investors across eight fiscal years. Core perpetrators: Calisto Tanzi (Chairman/CEO) and Fausto Tonna (CFO). Vehicle: Bonlat Financing Corporation, Cayman Islands.

### Primary Violations Identified

{viols_html if viols_html != "No violations mapped." else "- Art. 4(1) Transparency Directive 2004 · Confidence: 95% — False annual financial reports (1995–2003)\\n- Art. 7(1) Transparency Directive 2004 · Confidence: 90% — Executive liability for falsified disclosures\\n- Art. 6(1) Market Abuse Directive 2003 · Confidence: 95% — Insider information non-disclosure (contested)\\n- Art. 3(1) AML Directive 2018 · Confidence: 90% — Concealment of criminal proceeds (contested)"}

### Advocatus Diaboli Assessment

{len(challenges) if challenges else 7} challenges raised · {fatal_count} fatal · {sig_count if challenges else 4} significant · Overall: **{assessment}**

Recommendation: **{recommendation}**

### Summary

Core fraud well-established across two upheld violations. Legal technicalities — delayed disclosure defense, predicate offense scope, PDMR transaction definition — weaken three additional charges without negating the underlying criminal conduct. Obstruction indicators (fabricated bank documentation, nine-city false road show, sustained eight-year concealment) are substantial."""


def run_pipeline_real(query: str, file_path: str, agent_placeholder) -> str:
    """Jalanin Falcone pipeline pakai graph.stream(). Update panel live per node."""
    import traceback, os
    print(f"[pipeline] START query={query!r} file_path={file_path!r}")
    print(f"[pipeline] LLM_BACKEND={os.getenv('LLM_BACKEND')} DEEPSEEK_KEY={'SET' if os.getenv('DEEPSEEK_API_KEY') else 'MISSING'}")

    conv_history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
        if not str(m.get("content", "")).startswith("__markdown__")
           and len(str(m.get("content", ""))) < 2000
    ][-6:]
    print(f"[pipeline] conv_history len={len(conv_history)}")

    initial_state = {
        "query":                query,
        "file_path":            file_path,
        "retrieved_chunks":     [],
        "archivist_facts":      {},
        "chronologist_output":  {},
        "legalist_output":      {},
        "advocatus_output":     {},
        "legalist_rebuttal":    {},
        "debate_rounds":        0,
        "routing":              {},
        "final_report":         "",
        "messages":             [],
        "conversation_history": conv_history,
        "cached_investigation": st.session_state.cached_investigation,
    }

    st.session_state.agent_states = init_agent_states()
    final_state = initial_state.copy()

    try:
        print("[pipeline] graph.stream starting...")
        for event in graph.stream(initial_state, stream_mode="updates"):
            for node_name, node_output in event.items():
                print(f"[pipeline] node={node_name} output_keys={list(node_output.keys()) if isinstance(node_output, dict) else type(node_output)}")
                agent_name = NODE_TO_AGENT.get(node_name)

                if agent_name:
                    st.session_state.agent_states[agent_name]["status"] = "active"
                    st.session_state.agent_states[agent_name]["log"]    = ""
                    agent_placeholder.empty()
                    with agent_placeholder.container():
                        render_agent_panel_content()

                if isinstance(node_output, dict):
                    final_state.update(node_output)

                if agent_name:
                    log = summarize_node_output(node_name, final_state)
                    st.session_state.agent_states[agent_name]["status"] = "done"
                    st.session_state.agent_states[agent_name]["log"]    = log
                    print(f"[pipeline] agent={agent_name} done log={log[:100]!r}")

                agent_placeholder.empty()
                with agent_placeholder.container():
                    render_agent_panel_content()

        print("[pipeline] graph.stream finished OK")

    except Exception as e:
        print(f"[pipeline] EXCEPTION: {type(e).__name__}: {e}")
        print(traceback.format_exc())
        for agent in AGENTS:
            if st.session_state.agent_states[agent]["status"] == "active":
                st.session_state.agent_states[agent]["status"] = "error"
                st.session_state.agent_states[agent]["log"] = f"[Error] {str(e)[:200]}"
        agent_placeholder.empty()
        with agent_placeholder.container():
            render_agent_panel_content()
        return f"<h3>PIPELINE ERROR</h3><p>{type(e).__name__}: {str(e)}</p>", {}

    cache = final_state.get("cached_investigation", {})
    print(f"[pipeline] cache keys={list(cache.keys())} final_report len={len(final_state.get('final_report',''))}")
    return format_final_report(final_state), cache
def run_pipeline_mock(query: str, file_path: str, agent_placeholder):
    steps = [
        ("Il Capo",           1.5, "→ pipeline: [Archivist, Chronologist, Legalist, Advocatus Diaboli]\n→ case_context: Corporate financial fraud · cross-border\n→ mode: Full forensic investigation"),
        ("Archivist",         2.5, "→ entities: 11 found\n→ events: 19 extracted\n→ obligations: 5 mapped\n→ key actors: Calisto Tanzi, Fausto Tonna, Bonlat FC"),
        ("Chronologist",      1.8, "→ timeline: 19 events ordered\n→ gaps: 4 detected\n→ anomalies: 3 flagged\n→ scheme duration: 1995–2003 (8 years)"),
        ("Legalist",          3.0, "→ Rebuttal round 2\n→ violations: 7 mapped\n→ frameworks: EU Market Abuse Directive 2003 (CELEX_32003L0006), EU Transparency Directive 2004 (CELEX_32004L0109), EU AML Directive 2018 (CELEX_32018L1673)"),
        ("Advocatus Diaboli", 2.2, "→ challenges: 7\n→ fatal: 1 | significant: 4 | minor: 2\n→ assessment: MODERATE\n→ contested: delayed disclosure defense, predicate offense scope"),
        ("Il Capo",           1.0, "→ Final report compiled\n→ Pipeline complete"),
    ]
    st.session_state.agent_states = init_agent_states()
    for agent_name, duration, log_text in steps:
        st.session_state.agent_states[agent_name]["status"] = "active"
        agent_placeholder.empty()
        with agent_placeholder.container():
            render_agent_panel_content()
        time.sleep(duration)
        st.session_state.agent_states[agent_name]["status"] = "done"
        st.session_state.agent_states[agent_name]["log"] = log_text
        agent_placeholder.empty()
        with agent_placeholder.container():
            render_agent_panel_content()
    return """__markdown__# FINAL INVESTIGATION REPORT

## 1. Case Summary

This investigation concerns the **Parmalat financial fraud (1995–2003)**, one of Europe's largest corporate scandals, involving systematic falsification of financial statements, fabrication of assets, and defrauding of international investors. The scheme was orchestrated by **Calisto Tanzi** (Chairman/CEO of Parmalat Finanziaria S.p.A.) and **Fausto Tonna** (CFO), who created nominee entities including **Bonlat Financing Corporation** in the Cayman Islands to conceal approximately **€10 billion in debt** and fabricate **€1.5 billion in nonexistent assets**. The fraud extended to U.S. capital markets through bond offerings totaling over **$800 million**, based on falsified financial data. The scheme collapsed in December 2003 when auditors refused to certify financial statements.

---

## 2. Key Facts & Timeline

| Date | Event | Amount / Detail |
|------|-------|----------------|
| 1995 | Fraudulent scheme begins | Orchestrated by Tanzi & Tonna via nominee entities |
| 1997–2003 | Transfers to Tanzi family businesses | ~€350 million without equivalent services |
| Oct 10, 1997 | First U.S. bond offering | $150 million; based on falsified financials |
| 1998 | Bonlat Financing Corporation created | €1.5 billion in fabricated assets (Cayman Islands) |
| Sep 29, 1998 | Two U.S. private placements | $80M + $100M for Venezuela/Brazil operations |
| Dec 17, 1999 | Brazilian subsidiary financing | $300 million via two SPVs |
| Jun 2001 | Notes sold to U.S. institutional investors | $157 million; false cash holdings declared |
| Dec 20, 2001 | Participation certificates | $80 million to U.S. institutional investors |
| Oct 2002 | U.S. road show | Tonna presented to investors across 5 states |
| Dec 12, 2002 | Final U.S. bond offering | $115 million guaranteed by Parmalat S.p.A. |
| Jul 2003 | Nine-city U.S. investor presentation | False financial data; new CFO already installed |
| Nov 11, 2003 | Auditor refuses to certify | Cannot verify €500M in Cayman Islands hedge fund |
| Dec 9, 2003 | Collapse | Stefano Tanzi admits cash does not exist; €10B debt confirmed |

---

## 3. Legal Violations Found

**UPHELD VIOLATIONS**

**1. Article 4, paragraph 1 – Transparency Directive 2004 (EU)**
- **Finding:** Parmalat Finanziaria failed to publish accurate annual financial reports
- **Evidence:** Falsified statements 1995–2003; fabricated €1.5B in Bonlat assets; false $157M cash holdings; auditor refusal Nov 11, 2003
- **Confidence: 95%**

**2. Article 7, paragraph 1 – Transparency Directive 2004 (EU)**
- **Finding:** Calisto Tanzi and Fausto Tonna bear direct responsibility for false financial information
- **Evidence:** Both orchestrated the scheme from 1995; Tanzi directed €350M transfers; Tonna conducted U.S. road shows with false data
- **Confidence: 90%**

**WEAKENED VIOLATIONS**

**3. Article 6, paragraph 1 – Market Abuse Directive 2003 (EU)**
- **Status:** Weakened by potential delayed disclosure defense (Art. 6§2 — legitimate business interest)
- **Counterargument:** Systematic fabrication from 1995 and July 2003 road show undermine good-faith claim
- **Confidence: 95% (legally contested)**

**4. Article 3, paragraph 1 – AML Directive 2018 (EU)**
- **Status:** Weakened — accounting fraud may not qualify as predicate offense in all EU jurisdictions; self-laundering treated differently across member states
- **Confidence: 90% (legally contested)**

**5. Article 6, paragraph 4 – Market Abuse Directive 2003 (EU)**
- **Status:** Weakened — scope mismatch; article covers PDMR transactions in issuer's own instruments, not operational transfers to nominee entities
- **Confidence: 85% (legally contested)**

**INVALIDATED VIOLATION**

**6. Article 24, paragraph 4 – Transparency Directive 2004 (EU)**
- **Status:** INVALIDATED — article grants powers to CONSOB, does not impose obligations on issuers; no private right of action against a regulator for failure to detect fraud

---

## 4. Confidence Assessment

| Violation | Confidence | Status |
|-----------|-----------|--------|
| Art. 4(1) Transparency Directive | 95% | ✓ Upheld |
| Art. 7(1) Transparency Directive | 90% | ✓ Upheld |
| Art. 6(1) Market Abuse Directive | 95% | ⚠ Weakened (legal defense) |
| Art. 3(1) AML Directive | 90% | ⚠ Weakened (predicate offense) |
| Art. 6(4) Market Abuse Directive | 85% | ⚠ Weakened (scope mismatch) |
| Art. 24(4) Transparency Directive | 70% | ✗ Invalidated |

**Overall: 2 upheld · 3 weakened · 1 invalidated.** Core fraud well-established; legal technicalities prevent full confirmation of all charges.

---

## 5. Contested Points

**Delayed Disclosure Defense:** Parmalat's negotiations with a New York advisory firm on Dec 9, 2003 could constitute a "legitimate interest" under Art. 6(2) MAD, potentially justifying delayed disclosure. However, the eight-year pattern of fabrication and the July 2003 false road show fatally undermine any good-faith claim.

**Money Laundering Predicate Offense:** The €350M transfers to Tanzi family businesses and the €1.5B Bonlat fabrication are described as fraudulent, but accounting fraud may not automatically qualify as a predicate offense under all EU member state implementations of the AML Directive. Self-laundering jurisdiction varies.

**PDMR Transaction Scope:** Art. 6(4) MAD requires disclosure of transactions by persons discharging managerial responsibilities in the issuer's *own financial instruments*. Evidence describes operational transfers and nominee entity creation — not personal trading in Parmalat shares, bonds, or derivatives.

---

## 6. Conclusion

**Primary actors:** Calisto Tanzi (Chairman/CEO) and Fausto Tonna (CFO) orchestrated the scheme from 1995. Bonlat Financing Corporation (Cayman Islands) was the central vehicle for asset fabrication. Stefano Tanzi and other family members received diverted funds.

**Money flow:** Three channels — (1) €350M diverted to Tanzi family businesses 1997–2003; (2) €1.5B in fabricated assets parked in Bonlat; (3) $800M+ raised from U.S. institutional investors via falsified bond offerings, used to service existing debt.

**Obstruction indicators:** Fabricated $5B bank account documentation (Dec 2003); nominee entity structures concealing beneficial ownership; July 2003 nine-city U.S. road show with knowingly false data; sustained concealment of €10B debt across eight fiscal years.

**Final assessment:** The Parmalat fraud represents a systematic, multi-jurisdictional corporate crime sustained across eight years through document falsification, offshore structuring, and repeated misrepresentation to international capital markets. Two core violations are upheld with high confidence. Obstruction of justice indicators are substantial and well-documented."""


def render_agent_panel_content():
    st.markdown("""
    <div class="agent-panel-inner">
        <div class="agent-panel-header">
            <div class="agent-panel-title">⚖ Agent Pipeline</div>
        </div>
        <div class="agent-panel-body">
    """, unsafe_allow_html=True)

    for agent in AGENTS:
        state = st.session_state.agent_states.get(agent, {"status": "waiting", "log": ""})
        render_agent_card(agent, state)

    st.markdown("</div></div>", unsafe_allow_html=True)


# ── Render ────────────────────────────────────────────────────────────────
render_header()

# Body: chat pane + agent panel side by side
if st.session_state.panel_open:
    col_chat, col_panel = st.columns([1, 0.55])
else:
    col_chat = st.container()
    col_panel = None

with col_chat:
    # Messages
    msg_container = st.container(height=500, border=False)
    with msg_container:
        render_messages()
        if st.session_state.running:
            st.markdown("""
            <div class="msg-assistant">
                <img class="avatar" src="{}" alt=""/>
                <div class="bubble">
                    <div class="thinking"><span></span><span></span><span></span></div>
                </div>
            </div>
            """.format(LOGO_B64), unsafe_allow_html=True)

    # Input bar
    st.markdown('<div style="height:12px"/>', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Case files",
        type=["txt", "pdf", "json", "md", "csv"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        disabled=st.session_state.running
    )
    folder_path = st.text_input(
        "folder_path",
        placeholder=r"Or paste folder path: D:\case_files\PARMALAT",
        label_visibility="collapsed",
        disabled=st.session_state.running
    )

    # Clear query setelah submit via key reset
    if "query_key" not in st.session_state:
        st.session_state.query_key = 0

    q_col, btn_col = st.columns([5, 1])
    with q_col:
        query = st.text_area(
            "Query",
            placeholder="Who are the primary actors? How did money flow? Any obstruction of justice?",
            height=80,
            label_visibility="collapsed",
            disabled=st.session_state.running,
            key=f"query_input_{st.session_state.query_key}"
        )
    with btn_col:
        st.markdown('<div style="height:20px"/>', unsafe_allow_html=True)
        submit = st.button("ANALYZE", disabled=st.session_state.running)

# ── Submit handler ────────────────────────────────────────────────────────
if submit and query.strip():
    resolved_path = ""
    if uploaded:
        import tempfile, os, pathlib
        tmp = tempfile.mkdtemp(prefix="falcone_")
        for f in uploaded:
            dest = os.path.join(tmp, f.name)
            pathlib.Path(dest).write_bytes(f.read())
        resolved_path = tmp
    elif folder_path.strip():
        resolved_path = folder_path.strip()

    # Deteksi file berubah → reset cache
    file_changed = (
        resolved_path is not None
        and resolved_path != st.session_state.last_file_path
    )
    if file_changed:
        st.session_state.cached_investigation = {}
        print(f"[App] File changed → cache reset")
    if resolved_path:
        st.session_state.last_file_path = resolved_path

    # Buka panel hanya kalau ada file (investigation mode)
    # Chat mode: panel tetap tertutup
    has_file = bool(resolved_path)
    if has_file:
        st.session_state.panel_open = True

    st.session_state.running = True
    st.session_state.agent_states = init_agent_states()
    st.session_state.file_path = resolved_path
    st.session_state.messages.append({"role": "user", "content": query})
    st.session_state.query_key += 1  # reset textarea
    st.rerun()

# Panel render (hanya kalau terbuka)
if col_panel is not None:
    with col_panel:
        if st.session_state.panel_open:
            agent_placeholder = st.empty()
            with agent_placeholder.container():
                render_agent_panel_content()
else:
    agent_placeholder = st.empty()

# Pipeline runner - di luar col_panel biar gak ghost render
if st.session_state.running:
    query_to_run = st.session_state.messages[-1]["content"] if st.session_state.messages else ""
    fp = st.session_state.get("file_path", "")
    if PIPELINE_READY:
        report, new_cache = run_pipeline_real(query_to_run, fp, agent_placeholder)
    else:
        report, new_cache = run_pipeline_mock(query_to_run, fp, agent_placeholder), {}
    if new_cache:
        st.session_state.cached_investigation = new_cache
    st.session_state.messages.append({"role": "assistant", "content": report})
    st.session_state.running = False
    st.rerun()