import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Configuration Management Class.
    Securely loads API keys and model parameters from the environment.
    """
    
    # LLM Settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    
    # External API Keys
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")
    
    # Model Parameters
    DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "gpt-4o")
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.0"))
    
    @classmethod
    def validate(cls):
        """Validates that all required configuration variables are present."""
        missing = []
        if not cls.OPENAI_API_KEY and not cls.ANTHROPIC_API_KEY:
            missing.append("OPENAI_API_KEY or ANTHROPIC_API_KEY")
        
        if not cls.TAVILY_API_KEY:
            missing.append("TAVILY_API_KEY")
            
        if not cls.ALPHA_VANTAGE_KEY:
            missing.append("ALPHA_VANTAGE_KEY")
            
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
            
        print("Configuration validated successfully.")

# To test the validation during development
if __name__ == "__main__":
    try:
        Config.validate()
    except ValueError as e:
        print(f"Validation Error: {e}")
