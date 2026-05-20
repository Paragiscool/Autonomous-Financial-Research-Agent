import json
import os
from typing import Dict, Any, Callable

# ---------------------------------------------------------
# Mock Tool Stubs (Returning Hardcoded Mock Data)
# ---------------------------------------------------------

def sec_filing_search(ticker: str, filing_type: str, year: int = 2024) -> str:
    """Mock implementation of sec_filing_search."""
    return f"[MOCK SEC FILING] {filing_type} for {ticker} (Year: {year}).\nRisk Factors: Supply chain disruptions, market volatility.\nMD&A: Revenue grew by 15%."

def web_search(query: str, num_results: int = 10, date_range: str = None) -> str:
    """Mock implementation of web_search."""
    return f"[MOCK WEB SEARCH] Query: '{query}'.\n1. Article 1: Positive outlook on the market.\n2. Article 2: Analyst downgrades sector.\n(Returned {num_results} results)."

def financial_data_api(ticker: str, statement_type: str, period: str, years: int = 1) -> str:
    """Mock implementation of financial_data_api."""
    mock_data = {
        "ticker": ticker,
        "statement_type": statement_type,
        "period": period,
        "data": {
            "revenue": 383000000000,
            "net_income": 96000000000,
            "gross_margin": 0.45
        }
    }
    return f"[MOCK FINANCIAL DATA]\n{json.dumps(mock_data, indent=2)}"

def earnings_transcript(ticker: str, quarter: str, year: int) -> str:
    """Mock implementation of earnings_transcript."""
    return f"[MOCK EARNINGS TRANSCRIPT] {ticker} {quarter} {year}.\nCEO: We had a record breaking quarter.\nCFO: Operating expenses were kept under control."

def company_profile(ticker: str) -> str:
    """Mock implementation of company_profile."""
    profile = {
        "ticker": ticker,
        "name": f"{ticker} Inc.",
        "sector": "Technology",
        "market_cap": "2.5 Trillion USD",
        "description": "A leading technology company specializing in consumer electronics."
    }
    return f"[MOCK COMPANY PROFILE]\n{json.dumps(profile, indent=2)}"


# ---------------------------------------------------------
# Tool Registry Class
# ---------------------------------------------------------

class ToolRegistry:
    def __init__(self, schemas_dir: str = "tools/schemas"):
        self.schemas_dir = schemas_dir
        self.schemas: Dict[str, dict] = {}
        self.tools: Dict[str, Callable] = {
            "sec_filing_search": sec_filing_search,
            "web_search": web_search,
            "financial_data_api": financial_data_api,
            "earnings_transcript": earnings_transcript,
            "company_profile": company_profile
        }
        self._load_schemas()

    def _load_schemas(self):
        """Loads all JSON schemas from the schemas directory."""
        if not os.path.exists(self.schemas_dir):
            print(f"Warning: Schema directory '{self.schemas_dir}' not found.")
            return

        for filename in os.listdir(self.schemas_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.schemas_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        schema = json.load(f)
                        name = schema.get("function", {}).get("name")
                        if name:
                            self.schemas[name] = schema
                except Exception as e:
                    print(f"Failed to load schema {filename}: {e}")

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Validates the arguments against the schema (basic validation)
        and executes the corresponding tool stub.
        """
        if tool_name not in self.tools:
            return f"Error: Tool '{tool_name}' not found in registry."

        # Schema Validation: Check required params and enum values
        schema = self.schemas.get(tool_name)
        if schema:
            params_schema = schema.get("function", {}).get("parameters", {})
            properties = params_schema.get("properties", {})
            required_params = params_schema.get("required", [])

            # Check for missing required params
            missing_params = [p for p in required_params if p not in arguments]
            if missing_params:
                return f"Error: Missing required parameters for '{tool_name}': {', '.join(missing_params)}"

            # Check for invalid enum values
            for param, value in arguments.items():
                prop_def = properties.get(param, {})
                allowed_values = prop_def.get("enum")
                if allowed_values and value not in allowed_values:
                    return (f"Error: Invalid value '{value}' for parameter '{param}' in '{tool_name}'. "
                            f"Allowed values: {allowed_values}")

        # Execute Tool
        try:
            func = self.tools[tool_name]
            result = func(**arguments)
            return result
        except TypeError as e:
            return f"Error: Parameter mismatch for '{tool_name}'. {str(e)}"
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"


# Quick test when running the file directly
if __name__ == "__main__":
    registry = ToolRegistry(schemas_dir=os.path.join(os.path.dirname(__file__), "tools", "schemas"))
    
    print("Testing Tool Execution:")
    print("-" * 40)
    
    # Test 1: Valid Execution
    print(registry.execute_tool("sec_filing_search", {"ticker": "AAPL", "filing_type": "10-K"}))
    print("-" * 40)
    
    # Test 2: Missing required param
    print(registry.execute_tool("sec_filing_search", {"ticker": "AAPL"}))
    print("-" * 40)
    
    # Test 3: Financial Data API
    print(registry.execute_tool("financial_data_api", {"ticker": "AAPL", "statement_type": "income_statement", "period": "annual"}))
    print("-" * 40)
