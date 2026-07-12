"""Port (interface) for the LLM adapter."""

from abc import ABC, abstractmethod

from core.models import AIAnswer


class LLMPort(ABC):
    """Interface for LLM interactions."""

    @abstractmethod
    async def ask(self, prompt: str) -> AIAnswer:
        """Send a prompt to the LLM and return a structured answer."""
        ...
