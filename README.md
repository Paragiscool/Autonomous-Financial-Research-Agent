# ARA-1: Autonomous Financial Research Agent 📈

**QuantumEdge Research - Project 1A**

ARA-1 is a fully autonomous AI agent designed to replicate the workflow of a junior financial analyst. It receives complex research queries, independently formulates a research plan, gathers data from disparate sources (SEC filings, financial APIs, news feeds), and synthesizes its findings into structured investment reports.

## 🧠 Cognitive Architecture

ARA-1 utilizes a **Plan-and-Execute** framework powered by LangGraph, preventing infinite loops and context overflow. The architecture consists of:

1. **The Planner:** Breaks queries into numbered, dependency-mapped steps.
2. **The Executor:** Routes tasks to a 10+ Tool Registry using structured JSON schemas.
3. **The Synthesizer:** Resolves contradictory data using a strict Source Reliability Hierarchy.
4. **Three-Layer Memory:** Utilizes short-term context window management, long-term semantic storage via **ChromaDB**, and episodic strategy logging.

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────┐
│  Phase 0: Long-Term Memory Check (ChromaDB)     │
└───────────────────────┬─────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│  Phase 1: PLANNER (gpt-4o)                      │
│  → Generates structured, dependency-mapped plan │
└───────────────────────┬─────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│  Phase 2: EXECUTOR (step-by-step)               │
│  → Tool Registry (10+ tools, JSON schema)       │
│  → Enum + required-param schema validation      │
│  → Topological dependency resolver              │
│  → Fallback chains on tool failure              │
└───────────────────────┬─────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│  Phase 3: SYNTHESIZER                           │
│  → Multi-source conflict resolution             │
│  → Structured Investment Report (Markdown)      │
│  → Store findings back to ChromaDB              │
└─────────────────────────────────────────────────┘
```

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Agent Framework | LangChain & LangGraph |
| LLM | OpenAI `gpt-4o-mini` / `gpt-4o` |
| Vector Database | ChromaDB (Local Persistent) |
| Financial Data | SEC EDGAR API, yfinance |
| Search | Tavily Search API |
| Retry Logic | Tenacity (exponential backoff) |
| Token Tracking | tiktoken |
| Data Validation | Pydantic v2 |

## 📁 Project Structure

```
Finacial_agent/
├── agent/
│   ├── core.py          # Plan-and-Execute cognitive loop
│   ├── prompts.py       # System prompts (Planner / Executor / Synthesizer)
│   ├── parser.py        # LLM response JSON extractor (balanced-brace safe)
│   └── llm_wrapper.py   # RobustLLM with exponential backoff + token tracking
├── memory/
│   └── vector_store.py  # ChromaDB long-term memory (schema-enforced)
├── tools/
│   └── schemas/         # OpenAI function-calling JSON schemas (5+ tools)
├── tool_registry.py     # Tool registry with enum + required-param validation
├── config.py            # Secure env variable loader + validator
├── requirements.txt
├── pyproject.toml
├── .env.example         # API key template (never commit .env!)
├── ERROR_LOG.md         # Deliberate error tracking log
└── zetheta-project.json # Submission metadata
```

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

Open `.env` and add your API keys:
```
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
ALPHA_VANTAGE_KEY=...
```

**5. Run a dry-run test (no API keys needed)**
```bash
python agent/core.py
```

**6. Run with a real query (requires API keys)**
```python
from agent.core import AutonomousResearchAgent
from agent.llm_wrapper import RobustLLM

llm = RobustLLM(model_name="gpt-4o-mini")
agent = AutonomousResearchAgent(llm=llm, dry_run=False)
report = agent.research("Analyze Apple Inc.'s competitive position", ticker="AAPL")
print(report)
```

## 🔑 Required API Keys

| Key | Source | Required? |
|---|---|---|
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com) | ✅ Yes |
| `TAVILY_API_KEY` | [tavily.com](https://tavily.com) | ✅ Yes (web search) |
| `ALPHA_VANTAGE_KEY` | [alphavantage.co](https://alphavantage.co) | Optional |
| `SEC_USER_AGENT` | Your Name + Email | ✅ Yes (EDGAR is free) |

## 🧪 Running Tests

```bash
# Test the vector store (no API key needed)
python memory/vector_store.py

# Test the tool registry
python tool_registry.py

# Full agent dry-run (Challenge 1: Microsoft profile)
python agent/core.py
```

## 📊 Research Challenges (8 Progressive Tests)

| Challenge | Query Type | Status |
|---|---|---|
| 1 | Basic Company Profile (MSFT) | ✅ Dry-run passing |
| 2 | Financial Ratio Analysis | 🔄 Day 5 |
| 3 | Risk Assessment from SEC Filing | 🔄 Day 5 |
| 4 | Competitive Analysis (3 companies) | 🔄 Day 6 |
| 5 | Earnings Call Sentiment Analysis | 🔄 Day 7 |
| 6 | Multi-Source Conflict Resolution | 🔄 Day 8 |
| 7 | Full Investment Report | 🔄 Day 9 |
| 8 | Report Under Simulated Tool Failures | 🔄 Day 10 |

## 🤖 AI Assistance Policy Citation

During the development of this project, AI coding assistants were utilized for:
- Rapid scaffolding of Plan-and-Execute loop boilerplate.
- Generating regex patterns for JSON extraction in the parsing layer.
- Formatting standard JSON schemas for the Tool Registry.

*All architectural decisions, memory schemas, dependency resolution logic, and synthesis strategy were designed independently.*

---

*Zetheta Algorithms Private Limited — Project 1A Assessment*
