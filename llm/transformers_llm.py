import os
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from llm.base import FalconeLLM
from typing import Union
import torch

class TransformersBackend(FalconeLLM):
    """
    LLM backend based on Hugging Face Transformers.
    """
    def __init__(
        self,
        model_id: str = None,
        max_new_tokens: int = None,
        temperature: float = 0.1,
        device: str = "auto",
    ):
        self._model_id = model_id or os.getenv("TRANSFORMERS_MODEL_ID", "Qwen/Qwen2.5-72B-Instruct")
        max_tokens = max_new_tokens or int(os.getenv("TRANSFORMERS_MAX_TOKENS", 1024))
        
        self._tokenizer = AutoTokenizer.from_pretrained(self._model_id)
        model = AutoModelForCausalLM.from_pretrained(
            self._model_id,
            torch_dtype=torch.float16,
            device_map=device,
        )
        self._pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=self._tokenizer,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=temperature > 0,
        )

    def _to_prompt(self, prompt: Union[str, list]) -> str:
        """
        Convert input (plain string or message list) into a prompt string
        using the model's appropriate chat template.
        """
        if isinstance(prompt, list):
            return self._tokenizer.apply_chat_template(
                prompt,
                tokenize=False,
                add_generation_prompt=True,
            )
        return prompt

    def invoke(self, prompt: Union[str, list], max_new_tokens: int = None) -> str:
        prompt_str = self._to_prompt(prompt)
        result = self._pipe(prompt_str)
        return result[0]["generated_text"][len(prompt_str):]

    def stream(self, prompt: Union[str, list]):
        from transformers import TextIteratorStreamer
        import threading

        prompt_str = self._to_prompt(prompt)
        streamer = TextIteratorStreamer(self._tokenizer, skip_prompt=True)
        inputs = self._tokenizer(prompt_str, return_tensors="pt")
        thread = threading.Thread(
            target=self._pipe.model.generate,
            kwargs={**inputs, "streamer": streamer, "max_new_tokens": 1024}
        )
        thread.start()
        yield from streamer