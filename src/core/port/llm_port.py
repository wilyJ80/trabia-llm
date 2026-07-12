"""Port (interface) for the LLM adapter."""

from abc import ABC, abstractmethod

from core.models import AIAnswer


class LLMPort(ABC):
    """Interface for LLM interactions."""

    @abstractmethod
    async def ask(self, prompt: str) -> AIAnswer:
        """Send a prompt to the LLM and return a structured answer."""
        ...

    @abstractmethod
    async def ask_text(
        self,
        prompt: str,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> str:
        """Send a prompt to the LLM and return the raw text response."""
        ...
