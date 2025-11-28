from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseLLMProvider(ABC):
    """
    Abstract base for all LLM providers (OpenAI, Gemini, Ollama, etc.).
    """

    name: str

    def __init__(self, cfg: Dict[str, Any]) -> None:
        self.cfg = cfg or {}

    @abstractmethod
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        Return a list of models with metadata:
        [{"id": "gpt-4o", "tasks": ["chat","plan","edit"], ...}, ...]
        """
        raise NotImplementedError

    @abstractmethod
    async def execute(
        self,
        task: str,
        model: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a task (chat/plan/edit) with the given model.
        payload is free-form (messages, text, workflow, etc.)
        Should return a normalized response:
        {"role":"assistant","content":"...","raw": {...}}
        """
        raise NotImplementedError
