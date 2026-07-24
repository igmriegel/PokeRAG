"""
LLM Provider Abstraction Client.
"""

import logging
from openai import OpenAI
from pokemon_tcg_rag.config.settings import get_settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Wrapper client for OpenAI API interaction with error handling and fallback."""

    def __init__(self) -> None:
        settings = get_settings()
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model_name = settings.OPENAI_MODEL_NAME
        self.temperature = settings.OPENAI_TEMPERATURE

    def generate_answer(self, prompt: str) -> str:
        """Send formatted prompt to LLM and return generated response text."""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            logger.error("LLM Generation error: %s", exc)
            return "Ocorreu um erro ao comunicar com o servidor de IA. Por favor, tente novamente."
