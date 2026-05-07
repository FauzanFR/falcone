import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from llm.base import FalconeLLM
from llm.factory import get_llm as gl

load_dotenv()

_client = None
_embedder = None
_llm = None

def get_llm(backend: str = None, **kwargs) -> FalconeLLM:
    """
    Return the already-initialized LLM instance.
    Backend can be specified via parameter or the LLM_BACKEND env variable.
    """
    global _llm
    if _llm is None:
        _backend = backend or os.getenv("LLM_BACKEND", "deepseek")
        _llm = gl(_backend, **kwargs)
    return _llm

def get_client() -> QdrantClient:
    """Return the local Qdrant client."""
    global _client
    if _client is None:
        _client = QdrantClient(path=os.getenv("QDRANT_PATH", "./qdrant_db"))
    return _client

def get_embedder() -> SentenceTransformer:
    """Return the loaded BGE-M3 embedding model."""
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer('BAAI/bge-m3')
    return _embedder

def close():
    """Close the Qdrant connection."""
    global _client
    if _client is not None:
        _client.close()
        _client = None