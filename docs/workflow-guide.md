# Claude AI Skills & MCP Server Workflow Guide

A comprehensive guide for building Claude skills and Model Context Protocol (MCP) servers. This guide assumes zero prior knowledge and walks through everything from prerequisites to contributing your work back to the shared repository.

---

## Part 1: Prerequisites

Before you start building, ensure you have the right tools installed.

### System Requirements

- **Python 3.10 or higher**: Check your version with `python3 --version`
- **Git**: For version control. Install from https://git-scm.com
- **Text editor**: VS Code, Sublime Text, or any editor you prefer

### Package Manager: uv (Recommended)

We recommend **uv** — it's a fast Python package manager written in Rust. It installs dependencies much faster than pip and manages virtual environments automatically.

**Install uv:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

After installation, verify it works:

```bash
uv --version
```

**Fallback: pip**

If you prefer the standard package manager (comes with Python), you can use `pip` for everything in this guide. Replace any `uv pip` commands with `pip`.

### Claude Desktop

Download and install Claude Desktop from https://claude.ai. This is your primary interface for using skills and MCP servers.

**After installation:**
- Open Claude Desktop
- Look for "Settings" (usually gear icon in the top right)
- Note the path to your skills folder (you'll need it in Part 3)

### Claude Code (Optional, for Terminal Users)

If you want to use Claude from the terminal, install Claude Code:

```bash
npm install -g @anthropic-ai/claude-code
```

(Requires Node.js to be installed. Most developers skip this initially.)

### API Keys

You'll need API keys to power your MCPs:

#### Anthropic API Key (Required for Full Claude Access)

1. Go to https://console.anthropic.com
2. Sign in or create an account
3. Click "API keys" in the left sidebar
4. Click "Create key"
5. Copy the key and store it somewhere safe (your `.env` file, or environment variables)

In your terminal, set it:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

#### CBORG API Key (Free, for @lbl.gov Users)

CBORG is Lawrence Berkeley Lab's AI portal — free and keeps your data within LBL.

1. Go to https://cborg.lbl.gov
2. Sign in with your @lbl.gov account
3. Generate an API key in settings
4. Store it as an environment variable:

```bash
export CBORG_API_KEY="your-key-here"
```

(See Part 7 for how to use CBORG in your MCPs.)

---

## Part 2: Understanding Skills vs MCPs

This is crucial. Skills and MCPs serve different purposes — knowing which to use when is the foundation of this workshop.

### What is a Skill?

A **skill** is a markdown file (SKILL.md) that gives Claude specialized instructions and domain knowledge. Think of it as teaching Claude how to think about a particular domain.

**Key points:**
- Pure markdown — no code required
- Lives in your Claude skills folder
- Tells Claude WHAT to do and HOW to think
- Examples: "Research paper reading skill", "CRISPR biology skill", "Lab safety protocol skill"
- Activated when Claude detects relevant keywords or context

**Example scenario:**
You create a "Protein Structure Analysis" skill that teaches Claude best practices for interpreting PDB files, what questions to ask users, and how to format structural analysis results. When someone asks Claude about protein structures, Claude automatically uses this skill's guidance.

### What is an MCP Server?

An **MCP (Model Context Protocol) server** is a program that gives Claude new ABILITIES — it can call external APIs, query databases, run computations, access files, etc.

**Key points:**
- Written in Python (or TypeScript, but we focus on Python)
- Connected to Claude Desktop via configuration
- Tells Claude WHAT TOOLS ARE AVAILABLE and how to use them
- Examples: "Query PubMed API", "Check CBORG compute availability", "Access lab data warehouse"
- Can call real external services or run local code

**Example scenario:**
You create an MCP server that wraps the PubMed API. This gives Claude a tool called `search_pubmed` that it can invoke on demand. When a user asks Claude to search for papers, Claude calls your tool, which queries PubMed and returns results.

### When to Use Which?

| Use a Skill | Use an MCP Server |
|:---|:---|
| Teaching Claude domain knowledge | Accessing external APIs or databases |
| Workflow guidance and best practices | Running computations or scripts |
| Standard operating procedures | Querying real-time data |
| Analysis frameworks or checklists | Integrating with lab tools |
| No external tool access needed | Need to fetch/modify external data |

### The Power Combo: Skills + MCPs

Often, you'll use both together:

**Example: PaperBLAST Integration**
- **Skill**: "PaperBLAST best practices" — teaches Claude how to interpret BLAST results, what to check for, how to format findings for the lab
- **MCP**: "PaperBLAST API wrapper" — gives Claude a tool to query PaperBLAST in real-time and fetch results

Claude uses the skill's guidance while leveraging the MCP's ability to fetch live data.

---

## Part 3: Creating Your First Skill

Let's build a simple skill from scratch.

### Step 1: Locate Your Claude Skills Folder

Your skills folder is where Claude Desktop reads skill definitions.

**Find your skills folder:**

macOS:
```bash
~/Library/Application Support/Claude/skills/
```

Linux (if using Claude Desktop):
```bash
~/.config/Claude/skills/
```

Windows:
```
%APPDATA%\Claude\skills\
```

Verify it exists:
```bash
ls ~/Library/Application\ Support/Claude/skills/
```

(If the path doesn't exist, create it: `mkdir -p ~/Library/Application\ Support/Claude/skills/`)

**Alternative: Custom Skills Folder**

You can also set a custom path in Claude Desktop settings. Look for "Skills" or "Workspace" settings.

### Step 2: Create a Skill Directory

Create a folder for your skill with a clear name:

```bash
mkdir ~/Library/Application\ Support/Claude/skills/01-my-first-skill
cd ~/Library/Application\ Support/Claude/skills/01-my-first-skill
```

Naming convention: Start with a number for ordering, then use kebab-case (lowercase with hyphens).

### Step 3: Write Your SKILL.md

Create a SKILL.md file in your skill directory:

```bash
touch SKILL.md
```

Here's the template:

```markdown
# My First Skill

## Purpose

One sentence: what specialized knowledge or capability does this skill give Claude?

Example: "This skill teaches Claude best practices for analyzing genomic sequencing results and interpreting quality metrics."

## When to Use

Describe the keywords, contexts, or user requests that should trigger this skill. Claude will activate it automatically when these patterns match.

Examples:
- "When the user asks about genomic analysis"
- "When the user mentions sequencing quality"
- "When discussing variant calling"

## Instructions

Step-by-step instructions for Claude. Be specific:

### Questions to Ask the User

- What is the source of the data? (e.g., sequencer model, version)
- What is the goal of the analysis?
- Have quality metrics been reviewed?

### Key Practices

1. Always ask about the sequencing platform
2. Check read quality before proceeding
3. Validate coverage metrics (typically >30x for good quality)
4. Flag unusual quality patterns

### Output Format

Present results as:
- Summary line (one sentence)
- Key metrics (table or bullets)
- Interpretation (what do the metrics mean?)
- Recommendations (next steps)

### Common Mistakes to Avoid

- Don't assume coverage without asking
- Don't recommend analysis without knowing the experiment type
- Always verify the reference genome matches the organism

## Examples

### Example 1: User Question

**User:** "I have a sequencing run with 5 million reads. Is this good?"

**Claude's Response (using this skill):**

"To assess quality, I need more information:
- What organism or sample?
- What coverage do you need? (Research = 30x, clinical = 100x+)
- What platform? (Illumina, PacBio, etc.)

Once I understand your use case, I can evaluate the run properly."

### Example 2: User Question

**User:** "Our FASTQ files show Q30 of 85% across the run."

**Claude's Response (using this skill):**

"Q30 at 85% is good! This means 85% of bases have quality score >= 30 (one error per 1000 bases).

- Is this consistent across samples?
- What coverage did you achieve?
- Next step: Check for adapter contamination with FastQC"
```

### Step 4: Test Your Skill

1. Save SKILL.md
2. Open Claude Desktop
3. Ask Claude a question related to your skill's domain
4. Claude should activate the skill automatically based on keyword matching

Example: If you created a "Genomics" skill, ask Claude: "How do I interpret a quality report from my sequencer?"

Watch for Claude referencing your skill's instructions in its response.

### Step 5: Iterate and Refine

- If Claude isn't using your skill, the "When to Use" section might be too narrow. Make it more inclusive.
- If Claude's responses aren't following your format, make the "Output Format" more explicit.
- Test with different phrasings of the same question.

**Tips for improvement:**
- Add more keywords to "When to Use"
- Make instructions more prescriptive (use "always" instead of "consider")
- Include more detailed examples
- Test with non-experts from your lab to see if the instructions are clear enough

---

## Part 4: Creating Your First MCP Server

Now let's build a tool that Claude can actually use to call external APIs or run code.

### Step 1: Create Project Directory

```bash
mkdir my-first-mcp
cd my-first-mcp
```

### Step 2: Create pyproject.toml

This file describes your project and its dependencies.

```bash
touch pyproject.toml
```

Add this content:

```toml
[project]
name = "my-first-mcp"
version = "0.1.0"
description = "My first MCP server"
requires-python = ">=3.10"
dependencies = [
    "mcp[cli]>=1.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src"]
```

### Step 3: Create Directory Structure

```bash
mkdir -p src/my_first_mcp
touch src/my_first_mcp/__init__.py
touch src/my_first_mcp/server.py
```

### Step 4: Write Your First Tool (server.py)

In `src/my_first_mcp/server.py`:

```python
from mcp.server.fastmcp import FastMCP

# Create an MCP server instance
server = FastMCP("my-first-tool")

@server.tool()
def greet_user(name: str) -> str:
    """
    Greet a user by name.

    This is a simple example tool that Claude can call.
    Claude reads the docstring to understand what the tool does.

    Args:
        name: The person's name to greet

    Returns:
        A friendly greeting
    """
    return f"Hello, {name}! Welcome to MCP servers."


@server.tool()
def calculate_gc_content(sequence: str) -> dict:
    """
    Calculate GC content of a DNA sequence.

    This example shows how to return structured data.

    Args:
        sequence: DNA sequence (A, T, G, C characters only)

    Returns:
        Dictionary with gc_percent and sequence_length
    """
    sequence = sequence.upper()

    # Validate input
    valid_chars = set("ATGC")
    if not all(c in valid_chars for c in sequence):
        return {"error": "Invalid DNA sequence. Use only A, T, G, C."}

    # Calculate
    gc_count = sequence.count("G") + sequence.count("C")
    gc_percent = (gc_count / len(sequence)) * 100 if sequence else 0

    return {
        "gc_percent": round(gc_percent, 2),
        "sequence_length": len(sequence),
        "g_count": sequence.count("G"),
        "c_count": sequence.count("C"),
    }


if __name__ == "__main__":
    # Run the server on stdin/stdout
    # Claude Desktop will communicate with this server
    server.run()
```

### Step 5: Install Dependencies

Choose one:

**With uv (recommended):**
```bash
uv pip install -e .
```

**With pip:**
```bash
pip install -e .
```

The `-e` flag installs your package in "editable" mode, so changes to server.py take effect immediately.

### Step 6: Test the Server Standalone

Before connecting to Claude Desktop, test that your server works:

```bash
python src/my_first_mcp/server.py
```

You should see the server start. It's now listening on stdin/stdout. Press Ctrl+C to stop.

(If you get import errors like "ModuleNotFoundError: No module named 'mcp'", run the install command again.)

### Step 7: Register with Claude

Register your MCP server:

```bash
claude mcp add --scope user my-first-tool \
  python "$(pwd)/src/my_first_mcp/server.py"
```

The `$(pwd)` gives the absolute path automatically. The `--scope user` flag makes it available across all your projects.

To verify it's registered:
```bash
claude mcp list
```

### Step 8: Restart and Test

- If using Claude Desktop: close and reopen it
- If using Claude Code: start a new session (`claude`)
- If using Cowork: start a new task

### Step 9: Test Your Tool in Claude

Ask Claude to use your tool:

- "Greet me with the name Alice"
- "What's the GC content of ATGCATGCATGC?"

Claude should call your tool and return results.

### Troubleshooting

**Tool doesn't appear in Claude:**
- Run `claude mcp list` to verify the server is registered
- Check the path exists: `ls /absolute/path/to/server.py`
- Restart Claude Desktop (fully close and reopen)
- If you need to re-register: `claude mcp remove --scope user my-first-tool` then `claude mcp add` again

**"Module not found" errors:**
- Run `uv pip install -e .` again
- Check that you're in the correct directory (my-first-mcp)

**Tool appears but returns errors:**
- Check Claude Desktop's developer logs
- Add print statements to server.py to debug
- Run the server standalone to test: `python src/my_first_mcp/server.py`

---

## Part 5: Adding External API Calls to Your MCP

The real power of MCPs is calling external APIs. Let's build a tool that queries a real API.

### Example: PubMed Search Tool

Here's a practical example that searches PubMed for research papers.

**Create a new file** `src/my_first_mcp/pubmed.py`:

```python
import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

server = FastMCP("pubmed-search")

class SearchInput(BaseModel):
    """Input validation using Pydantic"""
    query: str = Field(description="PubMed search query (e.g., 'CRISPR gene editing')")
    max_results: int = Field(default=5, ge=1, le=20, description="Number of results (1-20)")


@server.tool()
async def search_pubmed(query: str, max_results: int = 5) -> str:
    """
    Search PubMed for research papers.

    Queries the NCBI PubMed database and returns a formatted list of papers
    with titles, authors, and abstracts.

    Args:
        query: Search query (e.g., "CRISPR gene editing")
        max_results: Maximum papers to return (1-20, default 5)

    Returns:
        Formatted string with paper titles and summaries
    """

    # API endpoint
    search_url = "https://pubmed.ncbi.nlm.nih.gov/api/search"

    try:
        # Make HTTP request (async)
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                search_url,
                params={
                    "term": query,
                    "retmax": max_results,
                    "rettype": "json",
                }
            )
            response.raise_for_status()

        # Parse JSON response
        data = response.json()

        if not data.get("result") or not data["result"].get("uids"):
            return f"No results found for: {query}"

        # Format results for Claude
        results = []
        for i, paper_id in enumerate(data["result"]["uids"][:max_results], 1):
            results.append(f"{i}. PMID: {paper_id}")

        return "\n".join(results) + f"\n\nFound {len(results)} papers. Use the PMID to look up full details."

    except httpx.TimeoutException:
        return f"Search timed out. Try a simpler query."
    except httpx.HTTPError as e:
        return f"API error: {str(e)}"


@server.tool()
async def get_pubmed_abstract(pmid: str) -> str:
    """
    Retrieve the abstract for a PubMed paper.

    Args:
        pmid: PubMed ID (numeric, e.g., "37654321")

    Returns:
        Paper title, authors, and abstract
    """

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://pubmed.ncbi.nlm.nih.gov/api/details",
                params={"uids": pmid}
            )
            response.raise_for_status()

        data = response.json()

        if not data.get("result") or not data["result"].get("uids"):
            return f"Paper not found: {pmid}"

        paper = data["result"][pmid]

        # Format nicely
        title = paper.get("title", "N/A")
        authors = paper.get("authors", [])
        abstract = paper.get("abstract", "No abstract available")

        author_str = ", ".join([a.get("name", "") for a in authors[:5]])
        if len(authors) > 5:
            author_str += f", and {len(authors) - 5} more"

        return f"""
**{title}**

Authors: {author_str}

Abstract: {abstract}
"""

    except httpx.HTTPError as e:
        return f"Error fetching abstract: {str(e)}"


if __name__ == "__main__":
    server.run()
```

**Update your pyproject.toml:**

Add httpx to dependencies:

```toml
dependencies = [
    "mcp[cli]>=1.0.0",
    "httpx>=0.24.0",
    "pydantic>=2.0",
]
```

**Install and test:**

```bash
uv pip install -e .
python src/my_first_mcp/pubmed.py
```

**Register the new server:**

```bash
claude mcp add --scope user pubmed-search \
  python "$(pwd)/src/my_first_mcp/pubmed.py"
```

Restart Claude Desktop or start a new Claude Code session.

**Ask Claude to search:**

"Find recent papers on CRISPR gene therapy"

Claude will call your `search_pubmed` tool and fetch real PubMed data.

### Error Handling Patterns

Always handle errors gracefully:

```python
@server.tool()
async def robust_api_call(query: str) -> str:
    """Tool with comprehensive error handling."""

    try:
        # Set timeout to avoid hanging forever
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://api.example.com/search",
                params={"q": query}
            )

            # Check HTTP status
            response.raise_for_status()
            data = response.json()

            # Validate response structure
            if not data.get("results"):
                return "API returned no results."

            return f"Found {len(data['results'])} results"

    except httpx.TimeoutException:
        return "Request timed out. The service may be slow. Try again?"

    except httpx.HTTPStatusError as e:
        # Distinguish rate limiting from other errors
        if e.response.status_code == 429:
            return "Rate limit exceeded. Wait a few seconds and try again."
        return f"API error {e.response.status_code}: {e.response.text}"

    except httpx.RequestError as e:
        return f"Network error: {str(e)}"

    except ValueError as e:
        return f"Invalid response format: {str(e)}"
```

### Using Environment Variables for API Keys

Store sensitive data in environment variables, not in code:

```python
import os
import httpx
from mcp.server.fastmcp import FastMCP

server = FastMCP("api-with-auth")

@server.tool()
async def call_protected_api(query: str) -> str:
    """Call an API that requires authentication."""

    api_key = os.environ.get("MY_API_KEY")
    if not api_key:
        return "Error: MY_API_KEY environment variable not set"

    headers = {"Authorization": f"Bearer {api_key}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            "https://api.example.com/search",
            params={"q": query},
            headers=headers
        )
        response.raise_for_status()
        return response.json()

if __name__ == "__main__":
    server.run()
```

**Set environment variables before running Claude Desktop:**

```bash
export MY_API_KEY="your-key-here"
open /Applications/Claude.app
```

Or add to your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
export MY_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="sk-ant-..."
export CBORG_API_KEY="your-cborg-key"
```

Then restart your terminal.

---

## Part 6: Contributing to the Workshop Repo

Once you've built a skill or MCP, share it with your lab by contributing to the shared repository.

### Step 1: Clone the Repository

First-time setup:

```bash
git clone git@github.com:ArkinLaboratory/ai-skills-workshop.git
cd ai-skills-workshop
```

(If you haven't set up SSH keys for GitHub, follow: https://docs.github.com/en/authentication/connecting-to-github-with-ssh)

### Step 2: Create a Feature Branch

Never commit directly to main. Create a branch:

```bash
git checkout -b add-my-skill-name
```

Use descriptive branch names (kebab-case, lowercase):
- `add-crispr-analysis-skill`
- `add-pubmed-search-mcp`
- `add-lab-safety-checklist`

### Step 3: Add Your Skill or MCP

**For skills:**

Navigate to the examples directory and find the skills folder:

```bash
ls examples/skills/
```

Create a new directory with a sequential number:

```bash
mkdir examples/skills/03-my-skill-name
cd examples/skills/03-my-skill-name
```

Copy your SKILL.md into this directory.

**For MCPs:**

```bash
mkdir examples/mcps/02-my-mcp-name
cd examples/mcps/02-my-mcp-name
```

Copy your entire MCP project here (server.py, pyproject.toml, etc.)

### Step 4: Create Required Files

**For both skills and MCPs**, create a README.md:

```markdown
# My Skill / MCP Name

One-line description of what this does.

## Setup

### Installation Steps

For skills:
1. Copy SKILL.md to your Claude skills folder
2. Restart Claude Desktop
3. Ask Claude something related to this skill

For MCPs:
1. Clone or download this directory
2. Install: `uv pip install -e .`
3. Register: `claude mcp add --scope user my-tool python /path/to/server.py`
4. Restart Claude Desktop or start a new Claude Code session
5. Ask Claude to use the tool

## Usage

Describe how to use it. Include example Claude prompts:

**Example 1:** "..."
**Example 2:** "..."

## Files

- SKILL.md / server.py: Main implementation
- README.md: This file

## Author

Your name, date created

## Notes

Any additional context or limitations.
```

### Step 5: Review Your Work

Before committing, verify everything is there:

```bash
# For a skill
ls examples/skills/03-my-skill-name/
# Should show: SKILL.md, README.md

# For an MCP
ls examples/mcps/02-my-mcp-name/
# Should show: server.py, pyproject.toml, README.md, and any other files
```

### Step 6: Stage and Commit

Stage your changes:

```bash
git add examples/skills/03-my-skill-name/
# or
git add examples/mcps/02-my-mcp-name/
```

Commit with a clear message:

```bash
git commit -m "Add my-skill: Brief one-line description of what it does"
```

Good commit messages:
- `Add crispr-analysis-skill: Teaches Claude to interpret CRISPR editing results`
- `Add pubmed-mcp: Tool to search PubMed and fetch abstracts`
- `Add lab-safety-skill: Step-by-step safety protocols for the Arkin Lab`

Bad commit messages:
- `Update stuff`
- `Final version`
- `Fix`

### Step 7: Push to GitHub

```bash
git push -u origin add-my-skill-name
```

The `-u` flag sets this branch as the "upstream" so future pushes are shorter.

### Step 8: Open a Pull Request

Go to https://github.com/ArkinLaboratory/ai-skills-workshop

GitHub will show a banner: "Compare & pull request" — click it.

**Fill out the PR template:**

```markdown
## Description

What does this skill/MCP do? One sentence.

## Type of Change

- [ ] New skill
- [ ] New MCP server
- [ ] Bug fix
- [ ] Documentation

## Testing

How did you test it? Include example prompts if applicable.

Example:
```
Claude: "Analyze this CRISPR edit"
Claude response: [Properly analyzed using my skill]
```

## Checklist

- [ ] I've included SKILL.md or server.py, pyproject.toml
- [ ] I've included a README.md with setup instructions
- [ ] I've tested it works in Claude Desktop
- [ ] I've followed the naming conventions (numbered, kebab-case)
```

### Step 9: Wait for Review

Lab members will review your PR. They might ask questions or request changes:

**If they ask for changes:**

1. Make the edits locally
2. Stage and commit: `git add ... && git commit -m "Address feedback: ..."`
3. Push: `git push`
4. The PR updates automatically

**Once approved:** A maintainer will merge your PR, and your contribution is live.

### Pulling Latest Changes from Main

Periodically, pull updates from the shared repo:

```bash
git checkout main
git pull origin main
```

Then create a new branch for your next contribution:

```bash
git checkout -b add-next-feature
```

---

## Part 7: Using CBORG as an Alternative Backend

If you're at Lawrence Berkeley Lab (@lbl.gov email), CBORG is a free AI service that keeps your data within LBL.

### What is CBORG?

CBORG is an OpenAI-compatible API hosted by LBL. You can use it instead of Anthropic's API for language models (though they're typically not Claude models).

**Advantages:**
- Free for @lbl.gov users
- Data stays within LBL
- OpenAI-compatible API (works with the `openai` Python package)

**Disadvantage:**
- Models are not Claude (usually Llama, or other open-source models)

### Getting a CBORG API Key

1. Go to https://cborg.lbl.gov
2. Log in with your @lbl.gov account
3. Navigate to settings or "API keys"
4. Generate a new key
5. Store it:

```bash
export CBORG_API_KEY="your-key-here"
```

### Using CBORG in Your MCP

If you need a language model within your MCP (e.g., to classify data or generate text), use CBORG:

```python
import os
import httpx
from openai import OpenAI, AsyncOpenAI
from mcp.server.fastmcp import FastMCP

server = FastMCP("cborg-powered-tool")

@server.tool()
async def classify_research_abstract(abstract: str) -> str:
    """
    Use CBORG to classify a research abstract by topic.

    This tool calls CBORG (LBL's AI service) to analyze the abstract.
    """

    api_key = os.environ.get("CBORG_API_KEY")
    if not api_key:
        return "Error: CBORG_API_KEY not set"

    # Create CBORG client (OpenAI-compatible)
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.cborg.lbl.gov",  # CBORG endpoint
    )

    try:
        response = client.chat.completions.create(
            model="lbl/llama",  # CBORG's Llama model (free)
            messages=[
                {
                    "role": "system",
                    "content": "Classify the following research abstract into one of: Biology, Chemistry, Physics, Engineering, or Other."
                },
                {
                    "role": "user",
                    "content": abstract
                }
            ],
            temperature=0.5,
            max_tokens=100,
        )

        classification = response.choices[0].message.content
        return f"Classification: {classification}"

    except Exception as e:
        return f"CBORG error: {str(e)}"


if __name__ == "__main__":
    server.run()
```

### Available Models

Check https://cborg.lbl.gov for the full list of available models. Common options:

- `lbl/llama`: Open-source Llama model (free, fast)
- `lbl/claude`: Claude models (if available through partnership)
- Others: Varies by lab partnership

### CBORG Endpoints

**Public endpoint:**
```
https://api.cborg.lbl.gov
```

**Internal endpoint (if on LBL VPN):**
```
https://api-local.cborg.lbl.gov
```

(Use the public endpoint by default unless you're on the VPN and need lower latency.)

---

## Part 8: Troubleshooting

Common issues and solutions:

### MCP Server Not Appearing in Claude Desktop

**Problem:** You registered the server with `claude mcp add`, but it doesn't show up in Claude.

**Solutions:**

1. **Verify registration:** `claude mcp list` — check that your server appears

2. **Check the path exists:** `ls /absolute/path/to/server.py`

3. **Restart Claude Desktop:** Fully close and reopen (don't just close the window)

4. **Re-register if needed:** `claude mcp remove --scope user my-tool` then `claude mcp add` again

### Import Error: No Module Named 'mcp'

**Problem:** Running server.py gives `ModuleNotFoundError: No module named 'mcp'`

**Solution:**

```bash
uv pip install -e .
```

If using pip:
```bash
pip install -e .
```

The `-e` flag installs the project in "editable" mode, making the dependencies available.

**If still failing:**

Install mcp explicitly:
```bash
uv pip install "mcp[cli]>=1.0.0"
```

### Permission Denied When Running Server

**Problem:** `Permission denied: /path/to/server.py`

**Solution:**

Make the file executable:
```bash
chmod +x /path/to/server.py
```

Or run it explicitly with Python:
```bash
python /path/to/server.py
```

### Tool Returns Errors or No Results

**Problem:** Claude calls your tool, but it returns an error or "None".

**Solutions:**

1. **Add debugging output:**
   ```python
   @server.tool()
   def my_tool(param: str) -> str:
       print(f"DEBUG: Tool called with param={param}")
       try:
           result = do_something(param)
           print(f"DEBUG: Result={result}")
           return result
       except Exception as e:
           print(f"DEBUG: Exception={e}")
           return f"Error: {str(e)}"
   ```

2. **Check Claude Desktop logs:**
   - Look for stderr output in Claude Desktop's developer tools
   - Run the server standalone to see error messages in your terminal

3. **Test standalone:**
   ```bash
   python server.py
   # Server runs on stdin/stdout
   # Ctrl+C to stop
   ```

### Skill Not Being Used by Claude

**Problem:** You created a skill, but Claude isn't using it.

**Solution:**

1. **Verify the file is in the right location:**
   ```bash
   ls ~/Library/Application\ Support/Claude/skills/
   ```

2. **Make sure SKILL.md exists:**
   ```bash
   ls ~/Library/Application\ Support/Claude/skills/01-my-skill/SKILL.md
   ```

3. **Restart Claude Desktop**

4. **Broaden the "When to Use" section:** Make keywords more inclusive:
   ```markdown
   ## When to Use

   - When discussing genomics
   - When analyzing sequencing data
   - When the user mentions "quality" or "reads" or "coverage"
   - Any genetics or bioinformatics query
   ```

5. **Ask Claude explicitly:**
   Instead of: "What's a good sequencing depth?"
   Try: "I'm doing genomic analysis. What's a good sequencing depth?"

### CBORG API Errors

**Problem:** When using CBORG, getting auth errors or connection refused.

**Solutions:**

1. **Verify the API key is set:**
   ```bash
   echo $CBORG_API_KEY
   ```
   Should print your key, not empty.

2. **Check VPN status:** If using the internal endpoint:
   ```
   https://api-local.cborg.lbl.gov
   ```
   You must be on LBL VPN. Use the public endpoint if off-campus:
   ```
   https://api.cborg.lbl.gov
   ```

3. **Verify the key is valid:** Test it with curl:
   ```bash
   curl -H "Authorization: Bearer $CBORG_API_KEY" \
     https://api.cborg.lbl.gov/v1/models
   ```

### Port Already in Use

**Problem:** Running multiple servers and getting "Address already in use"

**Solution:**

MCP servers use stdio, not ports. This error is rare, but if it occurs:

1. Make sure only one instance is running: `pkill -f server.py`
2. Close and reopen Claude Desktop
3. Try a different machine or user account

---

## Quick Reference

### File Locations

| What | Path |
|:---|:---|
| Claude skills folder | `~/Library/Application Support/Claude/skills/` |
| Claude skills | `~/.claude/skills/` |
| MCP registration | `claude mcp add --scope user <name> <command> [args]` |
| Workshop repo | Clone from: `git@github.com:ArkinLaboratory/ai-skills-workshop.git` |

### Commands You'll Use

```bash
# Create and test an MCP server
mkdir my-mcp && cd my-mcp
touch pyproject.toml server.py
uv pip install -e .
python server.py

# Clone the workshop repo
git clone git@github.com:ArkinLaboratory/ai-skills-workshop.git

# Contribute back
git checkout -b add-my-feature
git add examples/mcps/02-feature/
git commit -m "Add feature: description"
git push -u origin add-my-feature
# Then open PR on GitHub

# Set environment variables
export ANTHROPIC_API_KEY="sk-ant-..."
export CBORG_API_KEY="your-key"
```

### MCP Server Template

```python
from mcp.server.fastmcp import FastMCP

server = FastMCP("my-tool-name")

@server.tool()
def my_tool(input_param: str) -> str:
    """Describe what this tool does."""
    return f"Result for {input_param}"

if __name__ == "__main__":
    server.run()
```

### Skill Template

```markdown
# Skill Name

## Purpose
[One sentence of what Claude can do with this skill]

## When to Use
[Keywords or contexts that trigger this skill]

## Instructions
[Step-by-step guidance for Claude]

## Examples
[Show example Claude interactions]
```

---

## Next Steps

1. **Build your first skill:** Start with a simple domain knowledge skill in Part 3.
2. **Build your first MCP:** Create a tool that wraps a simple API in Part 4.
3. **Contribute:** Follow Part 6 to submit your work to the workshop repo.
4. **Iterate:** Ask for feedback, refine, and build more complex skills and MCPs.

Welcome to the workshop. Happy building!
