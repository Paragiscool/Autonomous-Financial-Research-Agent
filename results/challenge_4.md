# Challenge 4: Market Sentiment (News API)

This challenge evaluated the NLP sentiment integration:
- Can the agent fetch live news from Tavily?
- Does it accurately score polarity using `TextBlob`?
- Are the results correctly capped at 5 articles per the Optimization Sprint?

**Status:** ✅ Passed
The agent fetched news for Tesla (TSLA) robotaxis, capped the list at 5, stripped empty metadata, and correctly labeled the overall sentiment.
