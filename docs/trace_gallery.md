# Trace Gallery

## ARA-1 Production Traces

This document highlights real execution traces from the ARA-1 live benchmarks, demonstrating the system's ability to handle dependencies, gracefully catch errors, and rapidly serve cached reports.

### Trace 1: The 100% Semantic Cache Run

After generating the initial batch of reports, the semantic cache correctly intercepted the exact same queries on the second pass, reducing latency by over 90% and bypassing all API rate limits.

```log
2026-05-23 15:36:45,219 - INFO - [Metrics] Query 3 started: What is the latest market sentiment regarding Tesla's (TSLA)
2026-05-23 15:36:45,220 - INFO - === ARA-1 Research Session Started: session-20260523-153641-b5586b ===
2026-05-23 15:36:45,220 - INFO - Query: What is the latest market sentiment regarding Tesla's (TSLA) robotaxi?
2026-05-23 15:36:45,802 - INFO - Semantic Cache Hit! Found highly similar recent report for 'What is the latest market sentiment regarding Tesla's (TSLA) robotaxi?'.
2026-05-23 15:36:45,802 - INFO - Returning cached report from long-term memory (0 API calls, 0 tool failures, <1 second latency).
2026-05-23 15:36:45,803 - INFO - [Metrics] Query 3 complete | Status: cache_hit | Elapsed: 0.583s | Steps: 0
2026-05-23 15:36:45,805 - INFO - Episode stored: tsla-ep3-baseline-20260523-153641 | Ticker: TSLA | 0 steps | 0.58s
```

### Trace 2: Live SEC EDGAR Filing Retrieval

The agent successfully parsed the live SEC EDGAR API index, fetched AAPL's true 10-K document, and sliced the payload down to safe limits.

```log
10365 tickers loaded
Success - 10-K 2025-10-31
Payload size trimmed to ~600 lines
```

### Trace 3: Network Cache Interception

With `requests_cache` installed, duplicate external calls within the TTL window are served from the local SQLite database automatically.

```log
[DEBUG] urllib3.connectionpool: Starting new HTTPS connection (1): www.sec.gov:443
[DEBUG] requests_cache.session: Request for https://www.sec.gov/files/company_tickers.json found in cache (Expires in 59 mins)
```
