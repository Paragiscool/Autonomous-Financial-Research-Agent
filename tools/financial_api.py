import yfinance as yf
import json
import logging
import pandas as pd

logger = logging.getLogger(__name__)

class FinancialDataTool:
    def __init__(self):
        pass

    def fetch_financials(self, ticker: str, statement_type: str, period: str = "annual", years: int = 3) -> str:
        """
        Fetches financial statements using yfinance and formats them into LLM-friendly JSON.
        statement_type: 'income_statement', 'balance_sheet', 'cash_flow'
        period: 'annual' or 'quarterly'
        years: Number of recent periods to retrieve (defaults to 3 to save context tokens)
        """
        ticker = ticker.upper()
        ticker_obj = yf.Ticker(ticker)
        
        try:
            # 1. Map the requested statement to the correct yfinance property
            if statement_type == "income_statement":
                data = ticker_obj.financials if period == "annual" else ticker_obj.quarterly_financials
            elif statement_type == "balance_sheet":
                data = ticker_obj.balance_sheet if period == "annual" else ticker_obj.quarterly_balance_sheet
            elif statement_type == "cash_flow":
                data = ticker_obj.cashflow if period == "annual" else ticker_obj.quarterly_cashflow
            else:
                return json.dumps({"error": f"Invalid statement_type: {statement_type}. Use income_statement, balance_sheet, or cash_flow."})

            if data is None or data.empty:
                return json.dumps({"error": f"No {statement_type} data found for {ticker}."})

            # 2. Limit to the requested number of periods to save massive amounts of LLM tokens
            data = data.iloc[:, :years]
            
            # 3. Clean up the columns (convert complex pandas Timestamps to simple string dates)
            data.columns = [col.strftime('%Y-%m-%d') if isinstance(col, pd.Timestamp) else str(col) for col in data.columns]
            
            # 4. Drop rows where all values are NaN to eliminate noise
            data = data.dropna(how='all')
            
            # 5. Convert remaining NaNs to None (which becomes 'null' in JSON) so the LLM parses it correctly
            data = data.where(pd.notnull(data), None)

            # 6. Convert to a standard Python dictionary, then to JSON
            financial_dict = data.to_dict()
            
            return json.dumps({
                "ticker": ticker,
                "statement_type": statement_type,
                "period": period,
                "data": financial_dict
            })

        except Exception as e:
            logger.error(f"yfinance API Error for {ticker}: {e}")
            return json.dumps({"error": f"Failed to retrieve financial data: {str(e)}"})

# Quick test execution
if __name__ == "__main__":
    fin_tool = FinancialDataTool()
    print("Testing yfinance fetcher (Apple Income Statement - Last 2 Years)...")
    result = fin_tool.fetch_financials("AAPL", "income_statement", period="annual", years=2)
    
    # Parse and print beautifully so we can verify the structure
    parsed = json.loads(result)
    print(json.dumps(parsed, indent=2)[:1000] + "\n\n...[TRUNCATED FOR DISPLAY]")
