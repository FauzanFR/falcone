from llm.base import FalconeLLM

def get_llm(backend: str = "vllm", **kwargs) -> FalconeLLM:
    """
    Factory to instantiate the correct LLM backend.
    Available: "gguf", "transformers", "ollama", "openai", "vllm".
    """
    if backend == "gguf":
        from llm.gguf_llm import GGUFBackend
        return GGUFBackend(**kwargs)
    elif backend == "transformers":
        from llm.transformers_llm import TransformersBackend
        return TransformersBackend(**kwargs)
    elif backend == "ollama":
        from llm.ollama_llm import OllamaBackend
        return OllamaBackend(**kwargs)
    elif backend == "openai":
        from llm.openai_compatible import OpenAICompatibleBackend
        return OpenAICompatibleBackend(**kwargs)
    elif backend == "vllm":
        from llm.vllm_llm import VLLMBackend
        return VLLMBackend(**kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}")