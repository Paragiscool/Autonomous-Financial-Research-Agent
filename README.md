# ARA-1: Autonomous Financial Research Agent 📈

**QuantumEdge Research — Project 1A**

ARA-1 is a fully autonomous AI agent designed to replicate the workflow of a senior financial analyst. It receives complex research queries, independently formulates a multi-step research plan, gathers data from disparate sources (SEC EDGAR filings, financial APIs, real-time news feeds, web search), resolves conflicting data through a strict Source Reliability Hierarchy, and synthesizes findings into structured investment-grade reports — with a built-in Anti-Hallucination Shield to verify every number before publication.

---

## 🚦 Project Status

| Component | Status |
|-----------|--------|
| Plan-and-Execute Cognitive Loop | ✅ Live & Verified |
| 6-Tool Live Registry (SEC, yfinance, Web, News) | ✅ Live & Verified |
| Multi-Source Conflict Resolution Synthesizer | ✅ Live & Verified |
| Verifier (Anti-Hallucination Shield) | ✅ Live & Verified |
| Chaos Engineering Resilience (Challenge 8) | ✅ Live & Verified |
| Long-Term Semantic Memory (ChromaDB) | ✅ Live & Verified |

---

## ✨ Key Features

### 🧩 Multi-Source Synthesizer — Conflict Resolution Engine
When different data sources disagree (e.g., a Web Search article reports NVIDIA Q4 revenue as $19.0B while the official SEC 10-K shows $18.4B), the Synthesizer enforces a strict **Source Reliability Hierarchy** to resolve the conflict and select the correct figure:

```
[Tier 1] SEC Regulatory Filings (10-K, 10-Q) — ULTIMATE TRUTH
[Tier 2] Financial Data APIs (yfinance, income statements)
[Tier 3] Earnings Call Transcripts
[Tier 4] Major News Outlets / Web Search
[Tier 5] Social Media / Sentiment — Qualitative only
```

Every conflict is documented in a dedicated **"Research Notes & Discrepancies"** section of the final report. Verified live: Tier 1 SEC data ($18.4B) correctly overrode Tier 4 Web Search data ($19.0B).

---

### 🛡️ Verifier — Anti-Hallucination Shield
A post-generation editing node that acts as a strict Fact-Checking Editor. After the Synthesizer produces a draft, the Verifier:
1. Extracts every numerical claim, metric, and date from the draft report.
2. Cross-references each figure against the original raw JSON data payload.
3. Returns a structured JSON verdict: `{"is_verified": true/false, "hallucinations": [...]}`.
4. If hallucinations are detected, appends a **"Verifier Warnings"** section to the final report flagging each error for human review.

**Verified live:** Correctly passed a clean report and caught a deliberate `$18.5B` injection (actual: `$18.4B`) with three precise, sourced error descriptions.

---

### 💥 Chaos Engineering Resilient
ARA-1 passed the **Challenge 8 Chaos Engineering Gauntlet** — a stress test that injects a **50% random failure rate** into every tool call to simulate real-world API outages, network timeouts, and rate-limit drops.

```python
# Activate Hard Mode:
agent = AutonomousResearchAgent(llm=llm, dry_run=False, simulate_failures=True)
```

**Results:** All chaos-injected errors were gracefully caught, logged as `fallback_needed` in the findings JSON, and the downstream Synthesizer + Verifier pipeline continued without crashing the Python process.

---

## 🧠 Cognitive Architecture

ARA-1 implements a **Plan-and-Execute** framework with four sequential phases:

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  Phase 0: Long-Term Memory Check (ChromaDB)         │
│  → Skip redundant API calls for known tickers       │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│  Phase 1: PLANNER (Gemini 2.5 Flash)                │
│  → Generates structured, dependency-mapped plan     │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│  Phase 2: EXECUTOR (step-by-step)                   │
│  → 6-tool live registry (SEC/yfinance/Web/News)     │
│  → JSON schema validation (enum + required params)  │
│  → Topological dependency resolver                  │
│  → Soft-catch fallback on every tool failure        │
│  → Chaos Engineering mode (simulate_failures=True)  │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│  Phase 3: SYNTHESIZER (Conflict Resolution)         │
│  → 5-tier Source Reliability Hierarchy              │
│  → Structured Investment Report (Markdown)          │
│  → "Research Notes & Discrepancies" section         │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│  Phase 4: VERIFIER (Anti-Hallucination Shield)      │
│  → Cross-references every number vs raw JSON        │
│  → Appends Verifier Warnings if hallucinations found│
│  → Stores verified report to ChromaDB memory        │
└─────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Agent Framework | LangChain & LangGraph |
| LLM | Google Gemini 2.5 Flash (free-tier, 1M context) |
| Vector Database | ChromaDB (Local Persistent) |
| Financial Data | SEC EDGAR API, yfinance |
| Search | Tavily Search API |
| News & Sentiment | NewsAPI + TextBlob |
| Retry Logic | Tenacity (exponential backoff, 5 attempts) |
| Data Validation | Pydantic v2 |
| Security | All credentials via `os.getenv` — zero hardcoded keys |

---

## 📁 Project Structure

```
Finacial_agent/
├── agent/
│   ├── core.py          # Plan-and-Execute cognitive loop (Phases 0–4)
│   ├── prompts.py       # System prompts: Planner / Executor / Synthesizer / Verifier
│   ├── parser.py        # LLM response JSON extractor (balanced-brace safe)
│   └── llm_wrapper.py   # RobustLLM with exponential backoff + token tracking
├── memory/
│   └── vector_store.py  # ChromaDB long-term memory (schema-enforced)
├── tools/
│   ├── sec_edgar.py     # Live SEC EDGAR filing fetcher
│   ├── financial_api.py # yfinance income statement / balance sheet tool
│   ├── web_search.py    # Tavily web search tool
│   ├── news_sentiment.py# NewsAPI + TextBlob sentiment analyser
│   └── schemas/         # OpenAI function-calling JSON schemas (6 tools)
├── tool_registry.py     # Tool registry: validation + chaos engineering mode
├── test_synthesizer.py  # Day 8/9: Conflict resolution & hallucination tests
├── test_chaos.py        # Day 11/12 Challenge 8: Chaos Engineering Gauntlet
├── config.py            # Secure env variable loader + validator
├── requirements.txt
├── .env.example         # API key template (never commit .env!)
├── ERROR_LOG.md         # Deliberate error tracking log (7 errors)
└── zetheta-project.json # Submission metadata
```

---

## 🚀 Setup & Installation

**1. Clone the repository**
```bash
git clone https://github.com/Paragiscool/Autonomous-Financial-Research-Agent.git
cd Autonomous-Financial-Research-Agent
```

**2. Set up the virtual environment**
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure Environment Variables**
```bash
cp .env.example .env
```

Open `.env` and add your keys (see Required API Keys below).

**5. Run a dry-run test (no API keys needed)**
```bash
python agent/core.py
```

**6. Run the Conflict Resolution Test (requires GOOGLE_API_KEY)**
```bash
python test_synthesizer.py
```

**7. Run the Chaos Engineering Gauntlet**
```bash
python test_chaos.py
```

**8. Run a real research query**
```python
from agent.core import AutonomousResearchAgent
from agent.llm_wrapper import RobustLLM

llm = RobustLLM()
agent = AutonomousResearchAgent(llm=llm, dry_run=False)
report = agent.research("Analyze NVIDIA's competitive position in AI chips.", ticker="NVDA")
print(report)
```

---

## 🔑 Required API Keys

| Key | Source | Required? |
|---|---|---|
| `GOOGLE_API_KEY` | [aistudio.google.com](https://aistudio.google.com) | ✅ Yes (Synthesizer & Verifier) |
| `TAVILY_API_KEY` | [tavily.com](https://tavily.com) | ✅ Yes (web search tool) |
| `SEC_USER_AGENT` | Your Name + Email (free) | ✅ Yes (EDGAR access) |
| `NEWSAPI_KEY` | [newsapi.org](https://newsapi.org) | Optional (news sentiment) |
| `ALPHA_VANTAGE_KEY` | [alphavantage.co](https://alphavantage.co) | Optional |

---

## 🧪 Test Suite

```bash
# Test the vector store (no API key needed)
python memory/vector_store.py

# Test the live tool registry
python tool_registry.py

# Full agent dry-run (Challenge 1: Microsoft profile)
python agent/core.py

# Day 8/9: Synthesizer conflict resolution + Verifier hallucination catch
python test_synthesizer.py

# Day 11/12 Challenge 8: Chaos Engineering Gauntlet (50% failure rate)
python test_chaos.py
```

---

## 📊 Research Challenges Progress

| Challenge | Query Type | Status |
|---|---|---|
| 1 | Basic Company Profile (MSFT) | ✅ Passing |
| 2 | Financial Ratio Analysis | ✅ Passing |
| 3 | Risk Assessment from SEC Filing | ✅ Passing |
| 4 | Competitive Analysis (3 companies) | ✅ Passing |
| 5 | Earnings Call Sentiment Analysis | ✅ Passing |
| 6 | Multi-Source Conflict Resolution | ✅ Live & Verified |
| 7 | Full Investment Report w/ Anti-Hallucination | ✅ Live & Verified |
| 8 | Report Under 50% Simulated Tool Failures | ✅ Live & Verified |

---

## 🤖 AI Assistance Policy Citation

During development, AI coding assistants were utilized for:
- Rapid scaffolding of Plan-and-Execute loop boilerplate.
- Generating regex patterns for JSON extraction in the parsing layer.
- Formatting standard JSON schemas for the Tool Registry.

*All architectural decisions, the Source Reliability Hierarchy design, memory schemas, dependency resolution logic, Synthesizer/Verifier prompt engineering, and Chaos Engineering test strategy were designed independently.*

---

*Zetheta Algorithms Private Limited — Project 1A Assessment*
