# Optimization Log

## ARA-1 Performance Optimization History

This document tracks key architectural decisions and optimizations made during the ARA-1 development sprint.

---

### Optimization 1: Query-to-Query Semantic Embedding

**Problem:** Initial implementation embedded the full 5-page markdown report as the ChromaDB vector. Short user queries produced cosine distances > 0.6 vs the long report vector, causing 100% cache miss rate.

**Fix:** Switched to embedding the **original user query** as the vector document. The full report is stored inside the metadata payload. This ensures Query-to-Query comparison, bringing distances to ≤ 0.2 for semantically similar queries.

**Impact:** Cache hit rate went from **0%** to **20%** on the benchmark suite.

---

### Optimization 2: Unix Epoch Timestamp for TTL

**Problem:** Date stored as a string (`"2026-05-23"`) made 48-hour TTL filtering mathematically impossible in ChromaDB's `$gte`/`$lte` numerical filters.

**Fix:** Replaced string dates with `int(time.time())` Unix Epoch integers in all metadata writes. TTL check became: `timestamp >= current_time - 172800`.

**Impact:** Cache expiration logic is now mathematically sound and fully testable.

---

### Optimization 3: Sequential Map-Reduce Compression

**Problem:** Concurrent `asyncio.gather()` on 50 data chunks triggered `429 Too Many Requests` on Gemini 15 RPM Free Tier, crashing the pipeline.

**Fix:** Refactored the `compress_data` loop to run strictly sequentially, processing one chunk at a time.

**Impact:** Eliminated all rate-limit errors. SEC EDGAR payloads reduced from ~26,000 chars to ~5,000 chars (≈80% reduction) before synthesis.

---

### Optimization 4: Ticker-Independent Caching

**Problem:** Memory storage was gated behind `if ticker:`, meaning all ticker-free queries were silently never stored in ChromaDB.

**Fix:** Added `safe_ticker = ticker if ticker else "unknown"` fallback so every query is cached regardless of whether a ticker was explicitly passed.

**Impact:** `evaluate.py` benchmark correctly registered 1 cache hit (20% ratio), meeting the target threshold.
