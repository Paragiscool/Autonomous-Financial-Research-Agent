# ERROR_LOG.md: Deliberate Errors Tracker

As per the Day 1 requirements, this log tracks the 7 deliberate factual or logical errors hidden within the project specification or discovered within the architectural design.

## Identified Errors

1. **Source Reliability Hierarchy Tier Reversal**
   - *Description:* The specification listed "Social media posts" as Tier 4 and "Major news outlets" as Tier 5. This is logically reversed.
   - *Correction:* Reordered news outlets to Tier 4 and social media/forums to Tier 5 in the Synthesizer prompt.

2. **Memory Utilization (AB-5) Math Error**
   - *Description:* The text described calculating the ratio of memory hits as "memory_hits multiplied by total_api_calls."
   - *Correction:* The metric was corrected to a division/ratio: `memory_hits / total_queries`.

3. **ChromaDB Vector Mismatch (Semantic Blowout)**
   - *Description:* Generating the semantic cache embedding vector using the full 5-page markdown report caused massive Cosine Distances for short queries, resulting in 0 cache hits.
   - *Correction:* Embedded the original user query as the Vector document and stored the full report inside the metadata payload.

4. **Timestamp Metadata Filtering Flaw**
   - *Description:* ChromaDB metadata filtering (`$gte`, `$lte`) relies on numerical comparisons, but the initial schema defined dates as strings (e.g., "2026-05-23"), making 48-hour expiration logic impossible.
   - *Correction:* Implemented explicit Unix Epoch integers (`int(time.time())`) in the metadata for mathematically safe `< 48 hours` cache checking.

5. **Map-Reduce API Rate Limit Blowout**
   - *Description:* Processing 50 data chunks concurrently triggered catastrophic `429 Too Many Requests` API drops on the Gemini 15 RPM Free Tier.
   - *Correction:* Refactored the `compress_data` loop to be strictly sequential, enforcing pacing to respect API budgets.

6. **Token Counter Object Crash**
   - *Description:* The custom telemetry token counter in `llm_wrapper.py` expected string inputs but crashed when fed an array of LangChain `HumanMessage` objects from the new memory compression layer.
   - *Correction:* Added instance type checking and recursive string extraction to the token counter logic.

7. **Ticker-Dependent Cache Bypass**
   - *Description:* The `research()` logic wrapped memory storage inside an `if ticker:` block. Queries like "What is the capital of France?" bypassed memory entirely because no ticker was detected.
   - *Correction:* Removed the strict requirement and implemented a `safe_ticker = ticker if ticker else "unknown"` fallback so every query is successfully cached.
