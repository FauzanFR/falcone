from abc import ABC, abstractmethod
from typing import Union

class FalconeLLM(ABC):
    """
    Abstract interface for LLM backends used by Falcone.
    Every backend must implement both `invoke` and `stream`.
    """

    @abstractmethod
    def invoke(self, prompt: Union[str, list], max_new_tokens: int = None) -> str:
        """
        Execute the LLM and return the complete response.
        `prompt` may be a plain string or a list of message dicts
        like [{"role": "user", "content": "..."}].
        """
        ...

    @abstractmethod
    def stream(self, prompt: Union[str, list]):
        """
        Execute the LLM in streaming mode, yielding text deltas one by one.
        """
        ...