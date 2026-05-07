import os
from langchain_ollama import ChatOllama
from llm.base import FalconeLLM
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from typing import Union

def _convert_messages(messages: list[dict]):
    """
    Convert plain dict messages into LangChain message objects
    (SystemMessage, HumanMessage, AIMessage).
    """
    result = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "system":
            result.append(SystemMessage(content=content))
        elif role == "user":
            result.append(HumanMessage(content=content))
        elif role == "assistant":
            result.append(AIMessage(content=content))
    return result

class OllamaBackend(FalconeLLM):
    """
    LLM backend using Ollama (local model via ChatOllama).
    """

    def __init__(
        self,
        model_path: str = None,
        n_threads: int = None,
        temperature: float = 0.1,
        num_ctx: int = None,
    ):
        self.llm = ChatOllama(
            model=model_path or os.getenv("OLLAMA_MODEL", "qwen3:8b"),
            temperature=temperature,
            num_ctx=num_ctx or int(os.getenv("OLLAMA_NUM_CTX", 32768)),
            think=False,
            num_thread=n_threads or int(os.getenv("OLLAMA_NUM_THREADS", 6)),
        )

    def invoke(self, prompt: Union[str, list], max_new_tokens: int = None) -> str:
        if isinstance(prompt, str):
            prompt = [{"role": "user", "content": prompt}]
        response = self.llm.invoke(_convert_messages(prompt))
        return response.content

    def stream(self, prompt: Union[str, list]):
        if isinstance(prompt, str):
            prompt = [{"role": "user", "content": prompt}]
        for chunk in self.llm.stream(_convert_messages(prompt)):
            yield chunk.content