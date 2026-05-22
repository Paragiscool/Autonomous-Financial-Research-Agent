import os
import logging
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Load environment variables from your .env file
load_dotenv()

# Set up basic logging so we can see the retries happening
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RobustLLM:
    def __init__(self, temperature=0.1):
        """
        Initializes the LLM wrapper using Gemini 2.5 Flash (free-tier via Google AI Studio).
        Model is resolved from the GOOGLE_API_KEY env variable — no hardcoded credentials.
        """
        self.model_name = "gemini-2.5-flash"
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=temperature
        )

    def count_tokens(self, text: str) -> int:
        """Returns a rough estimate of tokens in a text string without external downloads."""
        return len(text) // 4

    # We use Exception since Google GenAI might throw different exceptions than OpenAI
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        before_sleep=lambda retry_state: logger.warning(
            f"API Error. Retrying in {retry_state.next_action.sleep} seconds..."
        )
    )
    def generate(self, prompt: str) -> str:
        """Sends the prompt to the LLM with token tracking and retry protection."""
        token_count = self.count_tokens(prompt)
        logger.info(f"Sending prompt to {self.model_name} (approx {token_count} tokens)")
        
        # Invoke the LangChain Google model
        response = self.llm.invoke(prompt)
        return response.content

# Quick test block to ensure it works when you run this file directly
if __name__ == "__main__":
    test_llm = RobustLLM()
    print("Testing connection...")
    reply = test_llm.generate("Explain the difference between a 10-K and a 10-Q in one sentence.")
    print(f"Response: {reply}")
