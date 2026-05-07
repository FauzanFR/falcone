import os
from openai import OpenAI
from llm.base import FalconeLLM
from typing import Union
from dotenv import load_dotenv
load_dotenv()

class OpenAICompatibleBackend(FalconeLLM):
    """
    Generic LLM backend for any OpenAI-compatible API.
    Configure via environment variables:
      - OPENAI_API_KEY   (required)
      - OPENAI_BASE_URL  (default: "https://api.openai.com/v1")
      - OPENAI_MODEL     (default: "gpt-4o")
    Can be used for OpenAI, Groq, xAI, OpenRouter, DeepSeek, etc.
    """

    def __init__(
        self,
        model_name: str = None,
        max_tokens: int = 2048,
        temperature: float = 0.1,
    ):
        # Allow override via constructor, fallback to env
        self.model_name = model_name or os.getenv("OPENAI_MODEL", "gpt-4o")
        self.max_tokens = max_tokens
        self.temperature = temperature

        # Instantiate client with env‑driven base_url and api_key
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )

    def invoke(self, prompt: Union[str, list], max_new_tokens: int = None) -> str:
        tokens = max_new_tokens or self.max_tokens

        if isinstance(prompt, list):
            messages = prompt
        else:
            messages = [{"role": "user", "content": prompt}]

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=tokens,
            temperature=self.temperature,
        )

        # Log token usage when available
        usage = response.usage
        if usage:
            print(f"[{self.model_name}] prompt={usage.prompt_tokens:,} completion={usage.completion_tokens:,}")

        return response.choices[0].message.content

    def stream(self, prompt: Union[str, list], max_new_tokens: int = None):
        tokens = max_new_tokens or self.max_tokens

        if isinstance(prompt, list):
            messages = prompt
        else:
            messages = [{"role": "user", "content": prompt}]

        response = self.client.chat.completions.create(
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