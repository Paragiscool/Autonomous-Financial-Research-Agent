# Challenge 3: Live Tool Execution (SEC EDGAR)

This challenge tested the agent's ability to ingest official regulatory documents:
- Can the agent map a Ticker (AAPL) to an SEC CIK number?
- Can it retrieve the latest 10-K filing?
- Does the payload slicer cap the raw HTML to 8,000 characters to prevent context bloat?

**Status:** ✅ Passed
The agent retrieved AAPL's true 10-K (filed 2025-10-31), sliced it to 600 lines, and identified the primary risk factors.
