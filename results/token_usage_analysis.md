# Token Usage & Context Window Analysis

## ARA-1 Efficiency Report — Post-Optimization

This report documents the LLM token usage strategy employed by ARA-1 to maximize output quality while operating efficiently and safely, preventing hallucinations caused by bloated context windows.

### Token Budget Strategy & Optimizations

| Phase | Technique | Estimated Token Savings |
|---|---|---|
| Network Layer | **HTTP Local Caching (`requests_cache`)** | Avoids redundant tool calls on LLM retries (0 tokens/retry) |
| Pre-Synthesis | **Payload Slicing (Data Diet)** | ~67% reduction on SEC payloads (capped at 8k chars) |
| Web Search | **Top 5 Article Cap + Null Stripping** | Prevents long tails of irrelevant news |
| Financial Data | **Null/Empty Value Stripping (`_strip_empty`)** | ~20-40% smaller payload per JSON financial statement |
| Generation | **Deterministic Constraints (`max_tokens`)** | Prevents runaway LLM text generation via hard limits |

### Observed Payload Sizes (Before vs After)

| Data Source | Raw Payload Size | Post-Optimization Size | Impact |
|---|---|---|---|
| SEC EDGAR 10-K Filing | ~26,392 chars | ~8,000 chars (capped) | Massive context saving |
| yfinance Income Statement | ~5,933 chars | ~4,200 chars | Cleaned empty fields |
| Tavily Web Search (10 articles) | ~6,500 chars | ~3,000 chars | Capped to top 5 articles |

### LLM Generation Constraints

RobustLLM configures Gemini generation strictly by role:

- **Planner:** `temperature=0.0`, `max_output_tokens=512` (pure deterministic JSON)
- **Executor:** `temperature=0.1`, `max_output_tokens=256` (concise observation)
- **Synthesizer:** `temperature=0.2`, `max_output_tokens=1500` (readable markdown prose)
- **Verifier:** `temperature=0.0`, `max_output_tokens=256` (binary verdict)

### Conclusion

By stripping out fat *before* data hits the LLM and capping generation per role, the agent strictly stays within its token budgets, processes faster, and eliminates the risk of hallucination from context bloat.
