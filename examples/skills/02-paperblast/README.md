# PaperBLAST Skill + MCP Server

**Purpose**: Search the scientific literature about any protein, find characterized homologs, and predict metabolic capabilities — all from a Claude conversation.

**Difficulty**: Intermediate (uses a real MCP server that scrapes HTML from papers.genomics.lbl.gov)

**Time**: 20-30 min to install and test

> **Requires LBNL VPN**: papers.genomics.lbl.gov is protected by Cloudflare and requires an LBL network connection. [VPN setup instructions](https://commons.lbl.gov/spaces/itfaq/pages/132810873/VPN+Information).

## What's Here

| File | What It Does |
|------|-------------|
| `SKILL.md` | Teaches Claude about PaperBLAST, Curated BLAST, and GapMind: when to use each, workflow patterns, query tips |
| `scripts/paperblast_mcp.py` | MCP server with 5 tools that make HTTP requests to papers.genomics.lbl.gov CGI endpoints and parse HTML responses |
| `scripts/check_deps.py` | Dependency checker — run this first to verify your setup |
| `scripts/test_parser.py` | Live parser test against a known protein (P0AEZ3 / MinD) |
| `scripts/models.py` | Pydantic models for structured output (PaperBLASTResult, GapMindResults, GapMindOrganismIndex, etc.) |
| `INSTALL.md` | Step-by-step installation instructions with dependency verification |
| `TESTING.md` | Test suite and verification procedures |
| `USAGE-EXAMPLES.md` | Real-world usage examples and best practices |
| `pyproject.toml` | Project metadata and build configuration |
| `references/setup.md` | Detailed setup and extension guide |

## Tools Exposed

| Tool | Use Case | Input | Returns |
|------|----------|-------|---------|
| `paperblast_search` | Find papers about a protein | Sequence or identifier (UniProt, RefSeq, VIMSS) + max_hits (default 25) | PaperBLASTResult |
| `paperblast_gene_papers` | Get full paper list for a hit | detail_id from prior search hit | PaperBLASTResult |
| `curated_blast_search` | Find characterized proteins by function | Functional description + optional genome | PaperBLASTResult |
| `gapmind_check` | Predict metabolic pathway completeness | Analysis type (aa/carbon) + organism | GapMindResults or GapMindOrganismIndex |
| `gapmind_list_organisms` | List available GapMind organisms | Analysis type (aa/carbon) | GapMindOrganismIndex |

## Setup

See [INSTALL.md](INSTALL.md) for step-by-step installation instructions (dependencies, skill copy, MCP registration, verification).

Quick summary:
```bash
pip install httpx beautifulsoup4 lxml pydantic "mcp[cli]"
mkdir -p ~/.claude/skills/paperblast/scripts
cp SKILL.md ~/.claude/skills/paperblast/
cp scripts/paperblast_mcp.py scripts/models.py ~/.claude/skills/paperblast/scripts/
claude mcp add --scope user paperblast python3 ~/.claude/skills/paperblast/scripts/paperblast_mcp.py
```

## What This Teaches

- **Real-world MCP pattern**: Wrapping Perl CGI tools with no JSON API into structured MCP tools
- **HTML parsing**: Using BeautifulSoup with heuristic pattern matching when there's no clean API
- **Pydantic validation**: Type-safe input models with field validators
- **Structured output**: Pydantic output models for machine-readable results
- **Async HTTP**: Using httpx for non-blocking requests
- **Error handling**: Graceful degradation when the upstream server is slow or down
- **Skill + MCP pairing**: The SKILL.md teaches Claude *when* and *how* to use the tools; the MCP server provides the *ability*

## Extending

The `references/setup.md` file lists additional tools at papers.genomics.lbl.gov that can be wrapped using the same pattern: Fitness Browser, fast.genomics, SitesBLAST, Sites on a Tree, HMM Search.

## Credits

PaperBLAST is developed by Morgan Price at LBNL. Source: [github.com/morgannprice/PaperBLAST](https://github.com/morgannprice/PaperBLAST)
