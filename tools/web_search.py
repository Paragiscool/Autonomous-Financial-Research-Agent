import os
import json
import requests
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class WebSearchTool:
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        self.url = "https://api.tavily.com/search"

    def search(self, query: str, max_results: int = 5) -> str:
        """
        Executes a live web search using Tavily, optimized for LLM context windows.
        Returns a JSON string containing the most relevant article snippets.
        """
        if not self.api_key or self.api_key == "your_tavily_api_key_here":
            return json.dumps({"error": "TAVILY_API_KEY is missing in the .env file."})

        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic", 
            "include_raw_content": False # Keeps the response lightweight
        }

        try:
            # We use a standard POST request so we don't need to install extra libraries
            response = requests.post(self.url, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()

            # Extract only the essential fields to prevent token bloat
            extracted_results = []
            for item in data.get("results", []):
                extracted_results.append({
                    "title": item.get("title"),
                    "source": item.get("url"),
                    "snippet": item.get("content")
                })

            return json.dumps({
                "query": query,
                "results": extracted_results
            })

        except requests.exceptions.RequestException as e:
            logger.error(f"Web Search API Error for query '{query}': {e}")
            return json.dumps({"error": f"Failed to retrieve web search results: {str(e)}"})

# Quick test execution
if __name__ == "__main__":
    search_tool = WebSearchTool()
    print("Testing Tavily Web Search (Query: 'Microsoft OpenAI partnership latest news')...")
    result = search_tool.search("Microsoft OpenAI partnership latest news", max_results=3)
    
    parsed = json.loads(result)
    print(json.dumps(parsed, indent=2))
