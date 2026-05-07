def tools(retrieve=False, retrieve_by_article=False, code=False, list_files=False, read_file=False):
    """
    Return the tool instruction string based on requested capabilities.
    These instructions are appended to the agent's system prompt.
    """
    instructions = []

    if not any([retrieve, retrieve_by_article, code, list_files, read_file]):
        return ""

    if retrieve:
        instructions.append("""
### TOOL: retrieve
Search the legal corpus using semantic search.

**When to use:** You need to find relevant laws based on facts, events, or concepts.

**Format:**
<tool>retrieve</tool>
<input>{"query": "specific search query here", "top_k": 5, "jurisdiction": "IT"}</input>

**jurisdiction (optional):**
- "IT" → Italian law only (TUF/CONSOB)
- "EU" → EU directives only
- "UN" → UN conventions only
- omit → search all corpus

**Example:**
<tool>retrieve</tool>
<input>{"query": "disclosure obligations financial statements issuers", "top_k": 10, "jurisdiction": "EU"}</input>
""")
    
    if retrieve_by_article:
        instructions.append("""
### TOOL: retrieve_by_article
Fetch EXACT legal article by source document and article name.

**When to use:** You have a specific article citation and need to verify its content.

**Format:**
<tool>retrieve_by_article</tool>
<input>{"source": "CELEX_32017L1371", "article": "Article 3: Fraud affecting the Union's financial interests"}</input>

**Available sources:**
- "CELEX_32017L1371" → PIF Directive 2017 (Fraud against EU budget)
- "CELEX_32018L1673" → AML Directive 2018 (Money laundering, 3rd)
- "CELEX_32003L0006" → Market Abuse Directive 2003 (Insider dealing & manipulation)
- "CELEX_32004L0109" → Transparency Directive 2004 (Periodic reporting & disclosure)
- "CELEX_32015L0849" → AML Directive 2015 (4th, Beneficial ownership & due diligence)
- "reg_consob_1999_11971" → CONSOB Regulation 11971/1999 - TUF (Italian securities law)
- "UN_CONVENTION" → UN Palermo Convention

**Example:**
<tool>retrieve_by_article</tool>
<input>{"source": "CELEX_32003L0006", "article": "Article 6"}</input>
""")
    
    if code:
        instructions.append("""
### TOOL: code
Generate and execute Python code to process non-standard file formats.

**When to use:** You receive a file with .log, .csv, or custom format that needs parsing.

**Format:**
<tool>code</tool>
<input>{"file_path": "/path/to/file.log"}</input>

Then write Python code:
<code>
# Your parser here
# DO NOT use import statements
# Available: re, json, csv, Path, np, pd, file_path
result = ...
</code>

**Example:**
<tool>code</tool>
<input>{"file_path": "/kaggle/input/chat_export.txt"}</input>

<code>
with open(file_path, "r") as f:
    lines = f.readlines()
result = [line.strip() for line in lines if "ERROR" in line]
</code>
""")

    if list_files:
        instructions.append("""
### TOOL: list_files
List all available files within a specific directory.

**When to use:** Use this when you need to explore the contents of a folder or before reading a file to ensure it exists.

**Format:**
<tool>list_files</tool>
<input>{"folder_path": "path/to/directory"}</input>

**Example:**
<tool>list_files</tool>
<input>{"folder_path": "mnt/data/logs"}</input>
""")

    if read_file:
        instructions.append("""
### TOOL: read_file
Read and return the full text content of a specific file.

**When to use:** You have a specific file path and need to analyze its content.

**Format:**
<tool>read_file</tool>
<input>{"file_path": "path/to/file.txt"}</input>

**Constraint:**
- Only use for text-based files (.txt, .md, .json, .log, .csv)
- For large data files like .csv or .log, use the 'code' tool instead.

**Example:**
<tool>read_file</tool>
<input>{"file_path": "mnt/data/config.json"}</input>
""")

    # --- Parallel calling instruction ---
    instructions.append("""## PARALLEL TOOL CALLING
You have very limited iterations. To be efficient, you MUST make MULTIPLE tool calls
in a SINGLE response whenever possible. Stack them like:

<tool>retrieve</tool>
<input>{"query": "...", "top_k": 5}</input>

<tool>retrieve</tool>
<input>{"query": "...", "top_k": 5}</input>

repeatedly. All results will be returned together. DO NOT call tools one by one unless
you absolutely need the result of the first tool for the second one.
""")

    return "\n".join(instructions)