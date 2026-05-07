from qdrant_client.models import Filter, FieldCondition, MatchValue
import re, json, csv, builtins, numpy as np, pandas as pd
from pathlib import Path
from tools.one_time_call import get_embedder, get_client

embedder = get_embedder()
client = get_client()

def parse_json_safe(text: str, fallback: dict) -> dict:
    """
    Safely parse a string as JSON; return `fallback` on failure.
    Handles ```json fences and attempts regex extraction.
    """
    if not text:
        return fallback
    try:
        clean = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
        return json.loads(clean)
    except:
        match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', clean)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass
        return fallback

def retrieve(query: str, top_k: int = 5, jurisdiction: str = None) -> list[dict]:
    """
    Semantic search in Qdrant using the query embedding.
    Optionally filter by jurisdiction.
    """
    query_vector = embedder.encode(query).tolist()
    
    search_filter = None
    if jurisdiction:
        search_filter = Filter(
            must=[FieldCondition(
                key="jurisdiction",
                match=MatchValue(value=jurisdiction)
            )]
        )
    
    all_results = client.query_points(
        collection_name="falcone_corpus",
        query=query_vector,
        limit=top_k,
        with_payload=True,
        query_filter=search_filter,
    ).points
    
    return [
        {
            "text"        : r.payload["text"],
            "article"     : r.payload.get("article", ""),
            "paragraph"   : r.payload.get("paragraph", ""),
            "parent_title": r.payload.get("parent_title", ""),
            "source"      : r.payload.get("source", ""),
            "collection"  : "law",
            "jurisdiction": r.payload.get("jurisdiction", ""),
            "score"       : r.score,
        }
        for r in all_results
    ]

def retrieve_by_article(source: str, article: str) -> list[dict]:
    """
    Fetch exact article chunks from the corpus by source and article name.
    """
    def scroll(article_key):
        results, _ = client.scroll(
            collection_name="falcone_corpus",
            scroll_filter=Filter(
                must=[
                    FieldCondition(key="source", match=MatchValue(value=source)),
                    FieldCondition(key="article", match=MatchValue(value=article_key)),
                ]
            ),
            with_payload=True,
            limit=100,
        )
        return results

    results = scroll(article)
    
    # Fallback: strip subtitle after ":"
    if not results:
        article_key = article.split(":")[0].strip()
        if article_key != article:
            results = scroll(article_key)
    
    return [
        {
            "text"          : r.payload["text"],
            "article"       : r.payload.get("article", ""),
            "paragraph"     : r.payload.get("paragraph", ""),
            "parent_title"  : r.payload.get("parent_title", ""),
            "parent_titolo" : r.payload.get("parent_titolo", ""),
            "parent_capo"   : r.payload.get("parent_capo", ""),
            "parent_parte"  : r.payload.get("parent_parte", ""),
            "source"        : r.payload.get("source", ""),
            "jurisdiction"  : r.payload.get("jurisdiction", ""),
            "collection"    : "law",
        }
        for r in results
    ]

def extract_and_exec(response: str, file_path: str = None) -> str:
    """
    Extract <code> block from agent response, execute as Python,
    and return the result as a JSON string or plain text.
    """
    match = re.search(r'<code>(.*?)</code>', response, re.DOTALL)
    if not match:
        return None  # no code block
    
    code = match.group(1).strip()
    
    # Remove import lines for safety
    code = "\n".join(
        line for line in code.splitlines()
        if not line.strip().startswith("import") 
        and not line.strip().startswith("from")
    )
    
    allowed_globals = {
        "__builtins__": vars(builtins),
        "re": re,
        "json": json,
        "csv": csv,
        "Path": Path,
        "np": np,
        "pd": pd,
        "file_path": file_path,
    }
    local_vars = {}
    try:
        exec(code, allowed_globals, local_vars)
    except Exception as e:
        return f"[Parser error: {e}]"
        
    result = local_vars.get("result", None)
    
    if isinstance(result, list):
        result = json.dumps(result, ensure_ascii=False, indent=2)
    elif isinstance(result, dict):
        result = json.dumps(result, ensure_ascii=False, indent=2)
    elif not isinstance(result, str):
        result = str(result)
    
    return result

def list_files(folder_path: str) -> list:
    """List all files in a directory."""
    try:
        path = Path(folder_path.strip()).resolve()
        return [f.name for f in path.iterdir() if f.is_file()]
    except Exception as e:
        return [f"[Error listing files: {e}]"]

def read_file(file_path: str) -> str:
    """
    Read a text file with basic validation.
    Handles Windows/Linux paths and special characters.
    """
    path = Path(file_path).resolve()
    if path.is_dir():
        return "[Error: Path is a directory, not a file]"
    if not path.exists():
        return f"[Error: File not found - {path}]"
    if path.exists():
        return path.read_text(encoding="utf-8")
    
    parent = path.parent
    if parent.exists():
        cleaned = path.name.replace("’", "'")
        for f in parent.iterdir():
            if f.name.replace("’", "'") == cleaned:
                return f.read_text(encoding="utf-8")
    
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return f"[Error reading file: {e}]"