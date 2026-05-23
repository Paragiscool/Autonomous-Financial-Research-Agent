# Challenge 6: Semantic Caching (Memory)

This challenge tested the agent's ability to "remember" past research:
- Does the system calculate the cosine distance between the new query and past queries in ChromaDB?
- Does it correctly return a cached report if the distance is `< 0.2`?
- Does it bypass all live tool calls and LLM generation?

**Status:** ✅ Passed
During the benchmark, the repeat query for Microsoft's revenue was intercepted by the Semantic Cache, dropping latency from 36 seconds down to 0.4 seconds.
