# PaperBLAST MCP Server Setup

## Prerequisites

- Python 3.10+
- Network access to `papers.genomics.lbl.gov` (LBNL network or public internet)

## Install Dependencies

```bash
pip install httpx beautifulsoup4 lxml "mcp[cli]"
```

## Run the Server

### Local (stdio transport — for Claude Code / Cowork)

```bash
python scripts/paperblast_mcp.py
```

### Remote (HTTP transport — for shared lab use)

```bash
python scripts/paperblast_mcp.py --http
# Starts on http://localhost:8765
```

## Configure in Claude Code

Add to `~/.claude/settings.json` or project `.claude/settings.json`:

```json
{
  "mcpServers": {
    "paperblast": {
      "command": "python",
      "args": ["/path/to/paperblast-skill/scripts/paperblast_mcp.py"]
    }
  }
}
```

## Configure in Cowork

Install as a skill in `~/.claude/skills/` or the project skills directory.

## Extending to Other Tools

The same pattern applies to all CGI tools at papers.genomics.lbl.gov:

1. Identify CGI parameters (read source at github.com/morgannprice/PaperBLAST)
2. Write a Pydantic input model with typed fields and descriptions
3. Write an HTML parser for the results page
4. Register as an `@mcp.tool` in the server

### Tools to wrap next (priority order)

| Tool | CGI | Key params |
|------|-----|------------|
| Fitness Browser | fit.genomics.lbl.gov | gene, organism, condition |
| fast.genomics | fast.genomics.lbl.gov/cgi/search.cgi | query (sequence/ID) |
| SitesBLAST | papers.genomics.lbl.gov/cgi-bin/sites.cgi | query (sequence) |
| Sites on a Tree | papers.genomics.lbl.gov/cgi-bin/treeSites.cgi | query (sequence) |
| HMM Search | papers.genomics.lbl.gov/cgi-bin/hmmSearch.cgi | query (HMM or sequence) |

### HTML parsing strategy

These Perl CGI tools produce HTML with no consistent class/ID conventions.
The reliable parsing approach is:

1. Find structural anchors (tables, headers, links to known databases)
2. Extract data relative to those anchors
3. Use regex for specific patterns (identity %, PMIDs, accessions)
4. Always include the source URL so the user can verify against the live page
5. Write tests against saved HTML snapshots to detect when page structure changes
