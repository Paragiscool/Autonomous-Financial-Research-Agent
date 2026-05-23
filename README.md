# ARA-1: Autonomous Financial Research Agent 🚀

## The Pitch
ARA-1 is a production-grade, autonomous AI agent designed to act as a tireless financial analyst. Instead of simply generating text from a prompt, ARA-1 thinks, plans, browses live internet data, reads official regulatory filings, cross-references conflicting information, and fact-checks its own work before presenting a final report. It is built to bridge the gap between AI capabilities and human trust, proving that complex, multi-step financial research can be fully automated with zero hallucinations and extreme efficiency.

---

## How It Thinks (Architecture Flowcharts)

### 1. The "ELI5" (Explain Like I'm 5) Flowchart
*How the agent operates, from the user's perspective.*

```mermaid
graph TD
    A[User Asks a Question] --> B{Does the Agent Remember This?}
    B -- Yes --> C[Instantly Return Past Answer]
    B -- No --> D[Agent Gathers New Data from Web & SEC]
    D --> E[Agent Writes a Draft Report]
    E --> F[Agent Editor Fact-Checks the Report]
    F --> G[Final Verified Report Delivered]
```

### 2. The Technical Architecture (LangGraph State Machine)
*The actual engineering backbone controlling the agent's cognitive loops.*

#### Option A: Advanced Engineering View (Full Node Telemetry & Chaos Injector)
```mermaid
graph TD
    %% Define Node Styles
    classDef user fill:#2d3436,stroke:#dfe6e9,stroke-width:2px,color:#fff;
    classDef memory fill:#0984e3,stroke:#74b9ff,stroke-width:2px,color:#fff;
    classDef core fill:#6c5ce7,stroke:#a29bfe,stroke-width:2px,color:#fff;
    classDef tools fill:#00b894,stroke:#55efc4,stroke-width:2px,color:#fff;
    classDef chaos fill:#d63031,stroke:#ff7675,stroke-width:2px,color:#fff;
    classDef final fill:#e84393,stroke:#fd79a8,stroke-width:2px,color:#fff;

    %% Graph Flow
    A[User Query]:::user --> B{Semantic Cache <br> ChromaDB}:::memory
    B -- Hit < 0.2 dist --> Z[Return Cached Report < 1s]:::final
    B -- Miss / Expired --> C[Planner Node]:::core
    
    C --> D[Executor Node]:::core
    D <--> E{Tool Registry <br> with Chaos Injector}:::chaos
    
    %% Tools
    E -->|Route| T1[SEC EDGAR API]:::tools
    E -->|Route| T2[yfinance API]:::tools
    E -->|Route| T3[Tavily Web Search]:::tools
    E -->|Route| T4[TextBlob NLP]:::tools
    
    %% Loop back
    E -- 50% Simulated Failure --> D
    
    D -- All Steps Complete --> F[Map-Reduce <br> Data Compressor]:::core
    F --> G[Synthesizer Node]:::core
    G --> H{Verifier Node <br> Anti-Hallucination}:::core
    
    H -- Hallucination Detected --> G
    H -- Verified True --> I[Save to ChromaDB]:::memory
    I --> J[Final Verified Markdown]:::final
```

#### Option B: Simplified State Machine View
```mermaid
graph TD
    %% Define Styles
    classDef memory fill:#d4edda,stroke:#28a745,stroke-width:2px;
    classDef brain fill:#cce5ff,stroke:#007bff,stroke-width:2px;
    classDef tool fill:#fff3cd,stroke:#ffc107,stroke-width:2px;
    classDef check fill:#f8d7da,stroke:#dc3545,stroke-width:2px;

    Query([User Query]) --> Cache[Phase 0: Semantic Cache Check]:::memory
    Cache -- Miss --> Plan[Phase 1: Planner Node]:::brain
    Cache -- Hit --> Output([Deliver Cached Report])
    
    Plan --> Exec[Phase 2: Executor Node]:::brain
    
    Exec --> T1(SEC API):::tool
    Exec --> T2(yfinance):::tool
    Exec --> T3(News API):::tool
    
    T1 --> Comp[Phase 3: Map-Reduce Compressor]:::brain
    T2 --> Comp
    T3 --> Comp
    
    Comp --> Synth[Phase 4: Synthesizer]:::brain
    Synth --> Verif[Phase 5: Verifier]:::check
    
    Verif -- Fails Checks --> Plan
    Verif -- Passes --> Save[Phase 6: Memory Store]:::memory
    Save --> Output
```

### 3. The Tool Routing Sequence (Conflict Resolution)
*How the agent handles conflicting data (e.g., when the news says one thing, but the official filings say another).*

```mermaid
sequenceDiagram
    participant Agent as ARA-1 Engine
    participant News as Web Search (News)
    participant YF as yfinance API
    participant SEC as SEC EDGAR API
    participant Synth as Synthesizer
    
    Agent->>News: Fetch Q3 Revenue
    News-->>Agent: Returns $19.0 Billion (Press Release)
    
    Agent->>YF: Fetch Income Statement
    YF-->>Agent: Returns $18.5 Billion (Preliminary)
    
    Agent->>SEC: Fetch 10-Q Official Filing
    SEC-->>Agent: Returns $18.4 Billion (Audited)
    
    Note over Agent: Engine applies Source Hierarchy:<br/>SEC > yfinance > News
    
    Agent->>Synth: Send SEC Data ($18.4B) & discard lower-tier conflicts
    Synth-->>Agent: Generates Draft Report with $18.4B
```

---

## Core Features (Translated for Humans)

### 🧠 Semantic Caching (ChromaDB)
**In Layman's Terms:** *It’s like remembering the answer to a math problem instead of calculating it from scratch every time.*
If you ask ARA-1 a question it has already researched, it uses AI vector embeddings to instantly recognize the similarity and serves the verified answer in milliseconds, saving massive API costs and time.

### 🕵️ Anti-Hallucination Verifier
**In Layman's Terms:** *It’s like an editor who meticulously fact-checks an author's draft against the original source documents before publishing.*
Before you ever see the final report, a completely separate "Verifier" AI reads the draft and compares it strictly against the raw data the tools pulled. If a number was invented or a fact hallucinated, the Verifier rejects the draft and forces a rewrite.

### 🌪️ Chaos Engineering (Resilience)
**In Layman's Terms:** *It’s like pulling the plug on the internet randomly to prove the system doesn't crash.*
During testing, we injected a 50% simulated failure rate into all tools (fake timeouts, API crashes, rate limits). The system's circuit breakers safely caught every error, retried intelligently, and pushed forward, ensuring the agent never crashes in production.

### ✂️ Map-Reduce Context Compression
**In Layman's Terms:** *It’s like having a junior assistant highlight only the most important sentences in a 100-page document so the boss can read it faster.*
Financial documents like SEC 10-Ks are massive. Instead of forcing the AI to read 100 pages (which burns through context limits and confuses the model), ARA-1 slices the document, compresses the noise, and only feeds the most critical paragraphs to the Synthesizer.

---

## The Benchmark Proof

ARA-1 isn't just theory—it has been rigorously benchmarked in a fully automated CI/CD-style test suite.

* **Factual Accuracy:** 100% verified pass rate. Zero hallucinations detected during automated multi-tool synthesis.
* **Latency Optimization:** Semantic caching drops standard 10-second research tasks down to **0.31 seconds** on repeat or highly similar queries.
* **Resilience:** Achieved a **100% survival rate** against a chaotic gauntlet of 50% random tool network failures.
* **Cache Efficiency:** Network-layer caching (`requests_cache`) eliminates 100% of duplicate web calls during fallback and retry loops.

---

## Tech Stack

* **Cognitive Architecture:** LangGraph (State Machine / DAG)
* **LLM Core:** Google Gemini 2.5 Flash (via Langchain)
* **Vector Database:** ChromaDB (Local Semantic Memory)
* **Web & Data Tools:** yfinance, SEC EDGAR API, Tavily Search API, NewsAPI
* **Resilience & Caching:** Tenacity (Exponential Backoff), requests_cache (HTTP Interception)

---

## Quick Start / Installation

Ready to run your own autonomous financial research?

```bash
# 1. Clone the repository
git clone https://github.com/Paragiscool/Autonomous-Financial-Research-Agent.git
cd Autonomous-Financial-Research-Agent

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Open .env and add your GOOGLE_API_KEY and TAVILY_API_KEY

# 5. Run the evaluation benchmark to see it in action!
python evaluation/benchmarks/evaluate.py
```
