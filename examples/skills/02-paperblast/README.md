# PaperBLAST Skill + MCP Server

**Purpose**: Search the scientific literature about any protein, find characterized homologs, and predict metabolic capabilities — all from a Claude conversation.

**Difficulty**: Intermediate (uses a real MCP server that scrapes HTML from papers.genomics.lbl.gov)

**Time**: 20-30 min to install and test

## What's Here

| File | What It Does |
|------|-------------|
| `SKILL.md` | Teaches Claude about PaperBLAST, Curated BLAST, and GapMind: when to use each, workflow patterns, query tips |
| `scripts/paperblast_mcp.py` | MCP server with 4 tools that make HTTP requests to papers.genomics.lbl.gov CGI endpoints and parse HTML responses |
| `scripts/check_deps.py` | Dependency checker — run this first to verify your setup |
| `scripts/test_parser.py` | Live parser test against a known protein (P0AEZ3 / MinD) |
| `references/setup.md` | Detailed setup and extension guide |

## Tools Exposed

| Tool | Use Case | Input |
|------|----------|-------|
| `paperblast_search` | Find papers about a protein | Sequence or identifier (UniProt, RefSeq, VIMSS) |
| `paperblast_gene_papers` | Get full paper list for a hit | Gene ID from prior search |
| `curated_blast_search` | Find characterized proteins by function | Functional description + optional genome |
| `gapmind_check` | Predict metabolic pathway completeness | Analysis type (aa/carbon) + organism |

## Setup

### 1. Check dependencies

```bash
cd examples/skills/02-paperblast/scripts
python check_deps.py
```

If anything fails:
```bash
pip install httpx beautifulsoup4 lxml "mcp[cli]"
```

### 2. Test connectivity

```bash
python check_deps.py --live
```

This makes a test request to papers.genomics.lbl.gov. If you get a Cloudflare error, connect to LBL VPN.

### 3. Add to Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "paperblast": {
      "command": "python",
      "args": ["/full/path/to/02-paperblast/scripts/paperblast_mcp.py"]
    }
  }
}
```

Copy the `SKILL.md` file and the full `02-paperblast` directory to your Claude skills folder.

Restart Claude Desktop.

### 4. Test it

Ask Claude: "Search PaperBLAST for papers about UniProt P0AEZ3"

Expected: Claude calls `paperblast_search`, gets structured results with homologous proteins and associated papers, and summarizes the findings.

## What This Teaches

- **Real-world MCP pattern**: Wrapping Perl CGI tools with no JSON API into structured MCP tools
- **HTML parsing**: Using BeautifulSoup with heuristic pattern matching when there's no clean API
- **Pydantic validation**: Type-safe input models with field validators
- **Async HTTP**: Using httpx for non-blocking requests
- **Error handling**: Graceful degradation when the upstream server is slow or down
- **Skill + MCP pairing**: The SKILL.md teaches Claude *when* and *how* to use the tools; the MCP server provides the *ability*

## Extending

The `references/setup.md` file lists additional tools at papers.genomics.lbl.gov that can be wrapped using the same pattern: Fitness Browser, fast.genomics, SitesBLAST, Sites on a Tree, HMM Search.

## Credits

PaperBLAST is developed by Morgan Price at LBNL. Source: [github.com/morgannprice/PaperBLAST](https://github.com/morgannprice/PaperBLAST)
