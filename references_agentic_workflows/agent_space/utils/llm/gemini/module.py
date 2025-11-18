import os
import logging
from typing import Optional

# Quiet known converter warnings from langchain-google-genai
try:
    logging.getLogger("langchain_google_genai").setLevel(logging.ERROR)
    logging.getLogger("langchain_google_genai._function_utils").setLevel(logging.ERROR)
except Exception:
    pass

from langchain_google_genai import ChatGoogleGenerativeAI
from variables.helper import ConfigLoader
from variables.google import GoogleConfig


class GeminiLLM:
    """
    Wrapper class providing a standardized interface to Google Gemini models
    within LangGraph or agentic runtimes.

    This class supports two authentication methods:
      - API key
      - Service Account key

    The class exposes a `.get_llm()` method callable by LangGraph that returns
    an instantiated ChatGoogleGenerativeAI client configured per request.

    Example:
        gem = GeminiLLM(load_mode="API")
        llm = gem.get_llm()
        response = llm.invoke("Hello!")

    Attributes:
        auth_mode (str): Authentication mode ("API" or "SA").
        credential (str): Loaded credential string.
        model (str): Gemini model name.
    """

    VALID_AUTH_MODES = {"API", "SA"}

    def __init__(self, auth_mode: str = "API", model: str = "gemini-2.5-flash"):
        """
        Initialize the GeminiLLM wrapper.

        Args:
            auth_mode (str): Authentication method ("API" or "SA").
            model (str, optional): Google Gemini model name.
        """
        if auth_mode not in self.VALID_AUTH_MODES:
            raise ValueError(
                f"Invalid auth_mode '{auth_mode}'. "
                f"Expected one of: {self.VALID_AUTH_MODES}"
            )

        google_cfg = ConfigLoader.load_single(GoogleConfig)

        self.auth_mode = auth_mode
        self.credential = (
            google_cfg["GOOGLE_GEMINI_API_KEY"]
            if auth_mode == "API"
            else google_cfg["GOOGLE_GEMINI_SERVICE_ACCOUNT"]
        )
        self.model = model

    def get_llm(
        self,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
        max_retries: int = 2,
        temperature: float = 0.0,
    ) -> ChatGoogleGenerativeAI:
        """
        Create a configured LangChain ChatGoogleGenerativeAI client instance.

        Args:
            max_tokens (Optional[int]): Maximum number of tokens to generate.
            timeout (Optional[int]): Optional timeout (seconds).
            max_retries (int): Automatic retry attempts for transient failures.
            temperature (float): Response randomness.

        Returns:
            ChatGoogleGenerativeAI: A fully configured LLM client.
        """
        os.environ["GOOGLE_API_KEY"] = self.credential

        return ChatGoogleGenerativeAI(
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            max_retries=max_retries,
        )

    def chat(self, message: str) -> str:
        """
        Convenience method to synchronously send a single message to Gemini.

        Args:
            message (str): User prompt text.

        Returns:
            str: Model-generated response text.
        """
        llm = self.get_llm()
        return llm.invoke(message)
