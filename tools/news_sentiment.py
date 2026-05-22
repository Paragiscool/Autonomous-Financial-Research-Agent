import json
import logging
from textblob import TextBlob
from tools.web_search import WebSearchTool

logger = logging.getLogger(__name__)

class NewsSentimentTool:
    def __init__(self):
        # We reuse your working Tavily search tool to grab the raw data!
        self.search_tool = WebSearchTool()

    def analyze_sentiment(self, query: str, max_articles: int = 5) -> str:
        """
        Fetches recent news articles for a query and performs NLP sentiment analysis.
        Returns a JSON string with individual and aggregated sentiment scores.
        """
        try:
            # 1. Fetch the raw news data (appending 'financial news' to focus the search)
            search_query = f"{query} financial news"
            search_result = self.search_tool.search(search_query, max_results=max_articles)
            search_data = json.loads(search_result)
            
            if "error" in search_data:
                return search_result  # Pass the error upward if Tavily fails

            articles = search_data.get("results", [])
            if not articles:
                return json.dumps({"query": query, "overall_sentiment": "Neutral", "score": 0.0, "articles": []})

            # 2. Analyze sentiment for each article
            total_polarity = 0.0
            analyzed_articles = []

            for article in articles:
                # Combine title and snippet for a more accurate NLP reading
                text_to_analyze = f"{article.get('title', '')}. {article.get('snippet', '')}"
                
                # TextBlob does the heavy lifting NLP math here
                blob = TextBlob(text_to_analyze)
                polarity = blob.sentiment.polarity
                
                # Assign a qualitative financial label
                if polarity > 0.15:
                    label = "Bullish"
                elif polarity < -0.15:
                    label = "Bearish"
                else:
                    label = "Neutral"
                    
                total_polarity += polarity
                
                analyzed_articles.append({
                    "title": article.get("title"),
                    "source": article.get("source"),
                    "polarity_score": round(polarity, 3),
                    "sentiment_label": label
                })

            # 3. Calculate the aggregate sentiment across all fetched articles
            avg_polarity = total_polarity / len(articles)
            if avg_polarity > 0.15:
                overall_label = "Bullish"
            elif avg_polarity < -0.15:
                overall_label = "Bearish"
            else:
                overall_label = "Neutral"

            return json.dumps({
                "query": query,
                "overall_sentiment_label": overall_label,
                "average_polarity_score": round(avg_polarity, 3),
                "articles": analyzed_articles
            })

        except Exception as e:
            logger.error(f"Sentiment Analysis Error for '{query}': {e}")
            return json.dumps({"error": f"Failed to analyze sentiment: {str(e)}"})

# Quick test execution
if __name__ == "__main__":
    sentiment_tool = NewsSentimentTool()
    print("Testing News Sentiment Analyzer (Query: 'Tesla Q3 delivery numbers')...")
    
    # We use a known volatile topic like Tesla deliveries to test the polarity scoring
    result = sentiment_tool.analyze_sentiment("Tesla Q3 delivery numbers", max_articles=3)
    
    parsed = json.loads(result)
    print(json.dumps(parsed, indent=2))
