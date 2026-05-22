import os
import json
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import logging

# Load the User-Agent from .env
load_dotenv()
SEC_USER_AGENT = os.getenv("SEC_USER_AGENT", "QuantumEdgeResearch admin@quantumedge.com")

logger = logging.getLogger(__name__)

class SecEdgarTool:
    def __init__(self):
        self.headers = {"User-Agent": SEC_USER_AGENT}
        self.tickers_url = "https://www.sec.gov/files/company_tickers.json"
        self.cik_map = self._load_cik_map()

    def _load_cik_map(self) -> dict:
        """The SEC API uses CIK numbers, not tickers. This maps Ticker -> CIK."""
        try:
            response = requests.get(self.tickers_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            # Creates a dictionary like {'AAPL': '0000320193'}
            return {item["ticker"]: str(item["cik_str"]).zfill(10) for item in data.values()}
        except Exception as e:
            logger.error(f"Failed to load SEC ticker map: {e}")
            return {}

    def fetch_filing(self, ticker: str, filing_type: str, year: int = None) -> str:
        """
        Retrieves the most recent filing text for a given ticker and type.
        """
        ticker = ticker.upper()
        if ticker not in self.cik_map:
            return json.dumps({"error": f"Ticker {ticker} not found in SEC database."})

        cik = self.cik_map[ticker]
        submissions_url = f"https://data.sec.gov/submissions/CIK{cik}.json"

        try:
            # 1. Get the list of recent filings
            response = requests.get(submissions_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            recent_filings = response.json().get("filings", {}).get("recent", {})

            # 2. Find the index of the requested filing type (e.g., "10-K")
            forms = recent_filings.get("form", [])
            accession_numbers = recent_filings.get("accessionNumber", [])
            primary_documents = recent_filings.get("primaryDocument", [])
            filing_dates = recent_filings.get("filingDate", [])

            target_index = -1
            for i, form in enumerate(forms):
                if form == filing_type:
                    if year and not filing_dates[i].startswith(str(year)):
                        continue
                    target_index = i
                    break

            if target_index == -1:
                return json.dumps({"error": f"No {filing_type} filing found for {ticker} in {year or 'recent history'}."})

            # 3. Construct the URL for the actual document
            accession_no = accession_numbers[target_index]
            accession_no_clean = accession_no.replace("-", "")
            document = primary_documents[target_index]
            doc_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_no_clean}/{document}"

            # 4. Fetch the HTML document and strip tags
            doc_response = requests.get(doc_url, headers=self.headers, timeout=20)
            doc_response.raise_for_status()
            
            soup = BeautifulSoup(doc_response.content, "html.parser")
            clean_text = soup.get_text(separator="\n", strip=True)

            # 5. Truncate to prevent context overflow (returning the first ~25k characters of MD&A/Risk Factors)
            return json.dumps({
                "ticker": ticker,
                "filing_type": filing_type,
                "date": filing_dates[target_index],
                "content_snippet": clean_text[:25000] + "\n...[CONTENT TRUNCATED FOR CONTEXT LIMITS]..."
            })

        except requests.exceptions.RequestException as e:
            logger.error(f"SEC API Error for {ticker}: {e}")
            return json.dumps({"error": f"Failed to retrieve data from SEC EDGAR: {str(e)}"})

# Quick test execution
if __name__ == "__main__":
    sec = SecEdgarTool()
    print("Testing SEC EDGAR Fetcher (Fetching Microsoft 10-K)...")
    result = sec.fetch_filing("MSFT", "10-K")
    print(f"Result snippet: {result[:500]}...")
