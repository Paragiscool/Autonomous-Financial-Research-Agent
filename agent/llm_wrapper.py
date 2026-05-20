import os
import tiktoken
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import openai

# Load environment variables from your .env file
load_dotenv()

# Set up basic logging so we can see the retries happening
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RobustLLM:
    def __init__(self, model_name="gpt-4o-mini", temperature=0.1):
        """
        Initializes the LLM wrapper. 
        We default to gpt-4o-mini for development to save costs, and a low temperature (0.1) 
        because financial research requires factual determinism, not high creativity.
        """
        self.model_name = model_name
        self.llm = ChatOpenAI(
            model=self.model_name,
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=temperature
        )
        # Load the correct tokenizer for the specified model.
        # Falls back to cl100k_base (GPT-4 family) for unknown model names.
        try:
            self.encoding = tiktoken.encoding_for_model(self.model_name)
        except KeyError:
            logger.warning(f"tiktoken: Unknown model '{self.model_name}'. Falling back to cl100k_base encoding.")
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Returns the exact number of tokens in a text string."""
        return len(self.encoding.encode(text))

    # The @retry decorator automatically intercepts specific API errors and waits 
    # before trying again. It starts at a 2-second wait and doubles up to 10 seconds, 
    # failing completely only after 5 attempts.
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((
            openai.RateLimitError, 
            openai.APIConnectionError, 
            openai.InternalServerError
        )),
        before_sleep=lambda retry_state: logger.warning(
            f"API Error. Retrying in {retry_state.next_action.sleep} seconds..."
        )
    )
    def generate(self, prompt: str) -> str:
        """Sends the prompt to the LLM with token tracking and retry protection."""
        token_count = self.count_tokens(prompt)
        logger.info(f"Sending prompt to {self.model_name} ({token_count} tokens)")
        
        # Invoke the LangChain ChatOpenAI model
        response = self.llm.invoke(prompt)
        return response.content

# Quick test block to ensure it works when you run this file directly
if __name__ == "__main__":
    test_llm = RobustLLM()
    print("Testing connection...")
    reply = test_llm.generate("Explain the difference between a 10-K and a 10-Q in one sentence.")
    print(f"Response: {reply}")
