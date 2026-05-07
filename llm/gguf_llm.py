import os
from langchain_community.llms import LlamaCpp
from llm.base import FalconeLLM
from typing import Union

def _messages_to_prompt(messages: list) -> str:
    """
    Convert a list of dict messages (role+content) into a prompt string
    using the Qwen2.5 chat template.
    """
    parts = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "system":
            parts.append(f"<|im_start|>system\n{content}<|im_end|>")
        elif role == "user":
            parts.append(f"<|im_start|>user\n{content}<|im_end|>")
        elif role == "assistant":
            parts.append(f"<|im_start|>assistant\n{content}<|im_end|>")
    parts.append("<|im_start|>assistant\n")  # trigger generation
    return "\n".join(parts)

class GGUFBackend(FalconeLLM):
    """
    Local LLM backend based on GGUF files via llama.cpp.
    """

    def __init__(
        self,
        model_path: str = None,
        n_ctx: int = None,
        n_threads: int = None,
        max_tokens: int = None,
        temperature: float = 0.1,
    ):
        self._llm = LlamaCpp(
            model_path=model_path or os.getenv("GGUF_MODEL_PATH", "./models/model.gguf"),
            n_ctx=n_ctx or int(os.getenv("GGUF_N_CTX", 32768)),
            n_threads=n_threads or int(os.getenv("GGUF_N_THREADS", 6)),
            max_tokens=max_tokens or int(os.getenv("GGUF_MAX_TOKENS", 1024)),
            temperature=temperature,
            n_gpu_layers=0,
            verbose=False,
        )

    def invoke(self, prompt: Union[str, list], max_new_tokens: int = None) -> str:
        if isinstance(prompt, list):
            prompt = _messages_to_prompt(prompt)
        return self._llm.invoke(prompt)

    def stream(self, prompt: Union[str, list]):
        if isinstance(prompt, list):
            prompt = _messages_to_prompt(prompt)
        return self._llm.stream(prompt)