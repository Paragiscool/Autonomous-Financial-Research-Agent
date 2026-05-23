# Architecture Specification (Final)

## ARA-1 System Design — v1.0.0

### Overview

ARA-1 implements a **Plan-and-Execute** cognitive architecture using LangGraph as the state machine backbone. Each phase is implemented as a discrete node with clearly defined inputs, outputs, and fallback behaviors.

### Phase Pipeline

| Phase | Node | Input | Output |
|---|---|---|---|
| 0 | Semantic Cache Check | User query string | Cached report or `None` |
| 0b | Long-Term Memory Check | User query + ticker | Prior findings JSON |
| 1 | Planner | Query + prior knowledge | Structured step plan (JSON) |
| 2 | Executor | Step plan | Raw findings list (JSON) |
| 3 | Map-Reduce Compressor | Raw findings list | Compressed findings list |
| 4 | Synthesizer | Compressed findings | Draft markdown report |
| 5 | Verifier | Draft report + raw findings | `{is_verified, errors}` |
| 6 | Memory Store | Query + verified report | Persisted ChromaDB entry |

### Tool Registry

| Tool ID | Source | Data Type |
|---|---|---|
| `company_profile` | yfinance | Company metadata |
| `financial_data_api` | yfinance | Income / balance sheet |
| `sec_filing_search` | SEC EDGAR EDGAR Full-Text API | 10-K / 10-Q filings |
| `web_search` | Tavily Search API | Live web results |
| `news_sentiment` | NewsAPI + TextBlob | Sentiment score + headlines |

### Reliability Hierarchy

```
[Tier 1] SEC Regulatory Filings (10-K, 10-Q) — ULTIMATE TRUTH
[Tier 2] Financial Data APIs (yfinance)
[Tier 3] Earnings Call Transcripts
[Tier 4] Major News Outlets / Web Search
[Tier 5] Social Media / Sentiment — Qualitative Only
```

### Semantic Cache Configuration

- **Embedding Model:** ChromaDB default (`all-MiniLM-L6-v2`)
- **Distance Threshold:** `<= 0.2` cosine distance (Query-to-Query matching)
- **TTL:** 48 hours (Unix Epoch integer comparison)
- **Storage Key:** Original user query (not the report)
