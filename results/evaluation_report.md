# Evaluation Report

## ARA-1 Quantitative Benchmark — Final Results

This report documents the results of the automated benchmark run executed via `evaluate.py` against 5 diverse financial research queries.

### Benchmark Summary

| Metric | Result | Target |
|---|---|---|
| Total Queries | 5 | 5 |
| Successful Runs | 5 / 5 | 5 / 5 |
| Cache Hits | 1 | ≥ 1 |
| Memory Utilization (Cache Ratio) | **0.20** | ≥ 0.20 ✅ |
| Total Tool Calls | 12 | — |
| Total Benchmark Time | 23.48s | — |
| Cached Query Latency | **0.31s** | < 1s ✅ |

### Query Breakdown

| # | Query | Result | Latency | Tool Calls |
|---|---|---|---|---|
| 1 | What is Microsoft's (MSFT) Q3 revenue? | ✅ Success | 7.58s | 3 |
| 2 | Summarize the risk factors from Apple's (AAPL) latest 10-K. | ✅ Success | 5.56s | 3 |
| 3 | What is the latest market sentiment regarding Tesla's (TSLA) robotaxi? | ✅ Success | 5.16s | 3 |
| 4 | What is Microsoft's (MSFT) Q3 revenue? *(Repeat — Cache Hit)* | ⚡ Cache Hit | 0.31s | 0 |
| 5 | Compare NVIDIA's (NVDA) data center growth with latest news. | ✅ Success | 4.86s | 3 |

### Key Findings

- **Semantic Cache** correctly identified the repeated MSFT query (cosine distance ≤ 0.2) and returned the cached report in 0.31 seconds with zero API calls.
- **Anti-Hallucination Verifier** passed all synthesized reports with zero hallucinations flagged.
- **Map-Reduce Compressor** pre-processed SEC EDGAR payloads (~26,000 characters) before each synthesis call, protecting the LLM context window budget.
