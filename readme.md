# Falcone AI

### *Forensic Document Intelligence System*

> *Named after Giovanni Falcone — the Italian anti-mafia judge who built cases methodically, stress-tested every claim, and never submitted until the evidence was solid.*

[![AMD MI300X](https://img.shields.io/badge/AMD-MI300X-ED1C24?style=flat&logo=amd)](https://www.amd.com/)
[![Built with Qwen](https://img.shields.io/badge/Model-Qwen2.5--72B-blue?style=flat)](https://huggingface.co/Qwen)
[![LangGraph](https://img.shields.io/badge/Framework-LangGraph-green?style=flat)](https://langchain-ai.github.io/langgraph/)
[![Qdrant](https://img.shields.io/badge/VectorDB-Qdrant-red?style=flat)](https://qdrant.tech/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?style=flat)](https://streamlit.io/)
[![lablab.ai](https://img.shields.io/badge/Hackathon-AMD%20Developer%20Challenge-ED1C24?style=flat)](https://lablab.ai/)

---

## What is Falcone?

Falcone is a **multi-agent forensic document intelligence system** designed to analyze financial crime documents and map violations against EU legal frameworks. It goes beyond simple RAG — it *debates its own findings* through an adversarial pipeline before producing a final report.

Upload a case file. Ask a question. Watch five specialized agents interrogate the evidence, challenge each other, and deliver a verdict grounded in real legal corpus.

---

## The Pipeline

```
Query + Document
       │
       ▼
  ┌─────────────┐
  │  IL CAPO    │  ← Routes: investigation or direct chat
  └──────┬──────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼        ┌──────────────┐
INVESTIGATE  CHAT ───► │ DIRECT ANSWER│ ← Il Capo answers directly
    │                  └──────────────┘
    ▼
┌──────────┐
│ARCHIVIST │  ← Extracts entities, events, obligations from documents
└────┬─────┘
     ▼
┌──────────────┐
│CHRONOLOGIST  │  ← Builds timeline, detects gaps and anomalies
└──────┬───────┘
       ▼
┌──────────┐
│ LEGALIST │  ← Retrieves relevant law, maps violations (RAG)
└────┬─────┘
     ▼
┌──────────────────┐
│ADVOCATUS DIABOLI │  ← Devil's advocate — challenges every finding
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
REBUTTAL   COMPILE
    │         │
    │         ▼
    │  ┌────────────┐
    │  │  IL CAPO   │  ← Synthesizes final investigation report
    │  └────────────┘
    │
    └──► Legalist defends
         │
         └──► back to ADVOCATUS (up to 2 rounds)
```

The Legalist-Advocatus debate loop runs up to **2 rounds** — Advocatus challenges the findings, Legalist rebuts with fresh retrieval, until the evidence either holds or collapses.

---

## Agents

| Agent                       | Role                                                                       |
| --------------------------- | -------------------------------------------------------------------------- |
| **Il Capo**           | Director. Routes queries, compiles final reports, handles direct legal Q&A |
| **Archivist**         | Extracts structured facts: entities, events, obligations, cross-references |
| **Chronologist**      | Builds event timeline, detects temporal gaps and behavioral anomalies      |
| **Legalist**          | RAG-powered legal analyst. Maps facts to EU directives and conventions     |
| **Advocatus Diaboli** | Devil's advocate. Stress-tests every violation claim for fatal weaknesses  |

---

## Interface

Falcone comes with a **Streamlit web UI** (`app.py`) for easy interaction:

- Upload documents (PDF, TXT, MD, JSON, CSV, LOG, etc.)
- Ask case-specific questions
- See real-time agent progress in the sidebar
- Receive the final report formatted in Markdown
- Continue follow-up conversations about the same case without re‑investigation

---

## Legal Corpus

Falcone's RAG corpus covers 7 EU/international legal frameworks:

| Source                    | Framework                                                     |
| ------------------------- | ------------------------------------------------------------- |
| `CELEX_32017L1371`      | PIF Directive 2017 — Fraud against EU financial interests    |
| `CELEX_32018L1673`      | AML Directive 2018 — Money laundering                        |
| `CELEX_32003L0006`      | Market Abuse Directive 2003 — Insider dealing & manipulation |
| `CELEX_32004L0109`      | Transparency Directive 2004 — Periodic reporting             |
| `CELEX_32015L0849`      | AML Directive 2015 — Beneficial ownership & due diligence    |
| `reg_consob_1999_11971` | CONSOB Regulation / TUF — Italian securities law             |
| `UN_CONVENTION`         | UN Palermo Convention — Transnational organized crime        |

---

## Tech Stack

| Component                  | Technology                 |
| -------------------------- | -------------------------- |
| **Inference**        | Qwen2.5-72B-Instruct (also supports OpenAI, DeepSeek, Groq, Ollama, etc.)       |
| **Hardware**         | AMD MI300X (192GB HBM3)    |
| **Orchestration**    | LangGraph (StateGraph)     |
| **Embeddings**       | BGE-M3 (BAAI)              |
| **Vector Store**     | Qdrant (local)             |
| **UI**               | Streamlit                  |
| **Document parsing** | Custom multi-format reader |

---

## Project Structure

```
falcone-ai/
├── app.py                  # Streamlit UI
├── prompts.py              # All system prompts for agents
├── env.example             # Template for environment variables
├── requirements.txt        # Python dependencies
├── one_time_setup.py       # Extracts pre-built Qdrant database
├── qdrant_db.zip           # Pre-built vector store (7 legal documents)
├── graph/
│   ├── graph.py            # LangGraph StateGraph builder
│   ├── state.py            # FalconeState TypedDict
│   └── _node.py            # All agent node functions
├── tools/
│   ├── tools.py            # Retrieve, retrieve_by_article, read_file, etc.
│   ├── core.py             # run_agent() agentic loop
│   ├── one_time_call.py    # Singleton: LLM, Qdrant client, embedder
│   └── prompts_tools.py    # Tool instruction strings for agents
├── llm/
│   ├── base.py             # FalconeLLM abstract class
│   ├── vllm_llm.py         # vLLM backend
│   ├── openai_compatible.py# OpenAI/DeepSeek/Groq/etc. backend
│   ├── ollama_llm.py       # Ollama backend
│   ├── gguf_llm.py         # GGUF backend
│   ├── transformers_llm.py # Transformers backend
│   └── factory.py          # get_llm() factory
└── qdrant_db/              # Local vector store (extracted from zip)
```

---

## Technical Walkthrough

### How It Works

1. **Routing** — Il Capo analyzes the query and decides: full investigation or direct answer?
2. **Fact Extraction** — Archivist reads uploaded documents (TXT, PDF, MD, JSON, CSV) and extracts structured facts via agentic tool-calling
3. **Timeline Construction** — Chronologist builds an event timeline, flags temporal gaps and suspicious patterns
4. **Legal Mapping** — Legalist performs RAG over 7 EU legal frameworks (BGE-M3 embeddings + Qdrant), maps facts to specific violations
5. **Adversarial Review** — Advocatus Diaboli challenges every violation claim; Legalist rebuts with fresh retrieval (up to 2 rounds)
6. **Final Report** — Il Capo compiles the investigation into a structured report with case summary, violations, contested points, and conclusion

### Key Design Decisions

- **Provider-agnostic LLM backend** — supports vLLM, Ollama, OpenAI, DeepSeek, Groq, GGUF, Transformers via a single factory pattern
- **Agentic tool-calling** — custom XML-based tool parser with parallel execution and 3-tier rescue parsing
- **Context window management** — automatic summarization + trimming prevents OOM on long investigations
- **Investigation caching** — follow-up questions reuse previous findings without re-running the pipeline
- **Temporal jurisdiction validation** — correctly identifies that laws enacted after a crime cannot apply (see Parmalat case)


---

## Setup

### 1. Clone & Install
```bash
git clone https://github.com/FauzanFR/falcone-ai.git
cd falcone
pip install -r requirements.txt
```

### 2. Configure environment
Copy the example environment file and edit it with your API keys/settings:
```bash
cp env.example .env
nano .env
```

### 3. Extract pre-built legal corpus (run once)

```bash
python one_time_setup.py
```
This unzips the pre-built Qdrant database containing all 7 legal documents, already chunked, embedded, and indexed. No ingestion needed.

### 4. Run the app

```bash
streamlit run app.py
```

---

## Usage

**Investigation mode** — upload a case document and ask:

* *"Who are the primary actors and what was their role?"*
* *"How did money flow from the company to offshore entities?"*
* *"What EU laws were violated, and do they apply given the timeline?"*
* *"Was there obstruction of justice?"*

**Chat mode** — ask without uploading a file:

* *"What is the Palermo Convention and what crimes does it cover?"*
* *"Explain the three stages of money laundering"*
* *"What's the difference between the PIF Directive and AML Directive?"*

---

## Demo Case: Parmalat (2003)

Falcone was tested on the Parmalat financial fraud — one of Europe's largest corporate scandals. Key findings from the pipeline:

* **Archivist** extracted 8 key entities, 12 events, 4 obligations
* **Chronologist** built a timeline from 1995–2003, flagging 3 gaps and 2 anomalies
* **Legalist** mapped 7 potential violations across 4 EU directives
* **Advocatus** challenged all 7 — invalidating 6 on temporal/jurisdictional grounds
* **Final verdict** : 1 validated violation (Market Abuse Directive 2003, Art. 1(2)), 6 invalidated. Recommendation: refer to Italian criminal courts and US SEC.

> *The system correctly identified that AML Directive 2018 and PIF Directive 2017 cannot apply to conduct that ended in 2003 — demonstrating legal rigor over hallucinated compliance.*

---

## Known Limitations

* **Prompt injection via document** — adversarial content embedded in uploaded files could influence agent behavior. Mitigated in future via input sanitization layer.
* **Temporal scope** — corpus covers directives as enacted; amendments and case law not included.
* **Language** — optimized for English-language documents. Multilingual support via Qwen's native capabilities but not explicitly tested.

---

## Built by

**Fauzan** — [@FauzanFR](https://github.com/FauzanFR)
Data Science student, Universitas Negeri Surabaya

*Built for the AMD Developer Hackathon on lablab.ai — AI Agents & Agentic Workflows track.*

---

*"The mafia is not invincible. It is a human fact, and like all human facts, it has a beginning and will have an end."*
*— Giovanni Falcone*
