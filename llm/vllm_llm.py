import os
from openai import OpenAI
from llm.base import FalconeLLM
from typing import Union

client_vllm = OpenAI(
    api_key="EMPTY",  # vLLM runs without a real API key
    base_url=os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1"),
)

class VLLMBackend(FalconeLLM):
    """
    LLM backend connected to a vLLM server (OpenAI-compatible API).
    """

    def __init__(
        self,
        model_name: str = os.getenv("VLLM_MODEL", "Qwen/Qwen2.5-72B-Instruct"),
        max_tokens: int = 2048,
        temperature: float = 0.1,
    ):
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature

    def invoke(self, prompt: Union[str, list], max_new_tokens: int = None) -> str:
        tokens = max_new_tokens or self.max_tokens

        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        else:
            messages = prompt

        response = client_vllm.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=tokens,
            temperature=self.temperature,
        )

        # Show token usage – useful for monitoring during hackathon
        usage = response.usage
        if usage:
            print(f"[vLLM] prompt={usage.prompt_tokens:,} completion={usage.completion_tokens:,}")

        return response.choices[0].message.content

    def stream(self, prompt: Union[str, list], max_new_tokens: int = None):
        tokens = max_new_tokens or self.max_tokens

        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        else:
            messages = prompt

        response = client_vllm.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=tokens,
            temperature=self.temperature,
            stream=True,
        )

        for chunk in response:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content