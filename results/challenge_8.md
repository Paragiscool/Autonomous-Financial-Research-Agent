# Challenge 8: Chaos Engineering (Resilience)

This challenge subjected the agent to extreme simulated network conditions:
- Can the agent survive a 50% random tool failure rate (`simulate_failures=True`)?
- Does the `requests_cache` correctly intercept Tenacity retries to prevent network thrashing?
- Does the Synthesizer still generate a report with partial data?

**Status:** ✅ Passed
The Python process never crashed. Errors were softly caught as `fallback_needed`, and the agent successfully generated reports despite massive missing context blocks.
