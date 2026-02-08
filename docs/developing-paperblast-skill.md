# Developing the PaperBLAST Skill: A Step-by-Step Story

This document walks through the full development lifecycle of the PaperBLAST skill — from initial product conception through design, implementation, debugging, testing, and team collaboration. It is intended as a teaching companion for the hackathon, showing the real decisions, mistakes, and debugging sessions that produced the working skill.

For reference material, see the companion docs:

- [What is a Skill?](what-is-a-skill.md) — conceptual overview
- [What is an MCP?](what-is-an-mcp.md) — protocol fundamentals
- [Skill Authoring Guide](skill-authoring-guide.md) — comprehensive design reference
- [Workflow Guide](workflow-guide.md) — setup, registration, contribution
- [PaperBLAST Skill Design Analysis](paperblast-skill-design.md) — retrospective analysis of the finished skill

---

## 1. Product Description: Why Build This?

### The Problem

[PaperBLAST](https://papers.genomics.lbl.gov) is a valuable tool that connects protein sequences to published literature. A researcher can paste a protein sequence or identifier and find papers about that protein and its homologs. The site also hosts Curated BLAST (finding characterized proteins by function in a target genome) and GapMind (predicting metabolic pathway completeness).

But the interface is a set of CGI web pages from the early 2000s. There is no REST API, no JSON output, no programmatic access. Every query requires visiting a browser, pasting input, and manually reading HTML results. If you want to check literature for 50 proteins from a metagenome, you are doing it one at a time.

### Why Not Just Ask Claude?

Claude can visit web pages and read HTML. Why not just say "go to papers.genomics.lbl.gov and search for P0AEZ3"?

Three problems with that approach. First, Claude's web access is unreliable for CGI-heavy sites, especially those behind Cloudflare. The pages require specific URL parameters and form submissions that browser automation handles poorly. Second, the raw HTML output is enormous — a single PaperBLAST search can return 2MB+ of HTML containing alignment visualizations, JavaScript event handlers, and nested tables. Claude's context window fills up fast. Third, there is no structure to parse. Claude would have to re-interpret the HTML every time, making errors and inconsistencies inevitable.

### Why a Skill + MCP?

A **skill** teaches Claude domain knowledge: what the tools do, when to use each one, what input formats work, and how to chain results together. Without the skill, Claude would need to rediscover the workflow every time.

An **MCP server** gives Claude reliable, structured access to the data. The server handles HTTP requests, parses the HTML into typed JSON, and returns clean results. The HTML parsing is done once, tested, and maintained in code — not re-improvised by the LLM on every call.

Together, a skill + MCP means Claude can answer "What papers exist about MinD in E. coli?" in a single tool call, returning structured JSON with gene entries, paper counts, identity percentages, and drill-down IDs — instead of trying to scrape a 200KB HTML page on the fly.

### The Product Specification

We defined five tools covering the three major PaperBLAST services:

| Tool | PaperBLAST Service | Purpose |
|------|-------------------|---------|
| `paperblast_search` | litSearch.cgi | Find papers about a protein by sequence or identifier |
| `paperblast_gene_papers` | litSearch.cgi?more= | Drill into the full paper list for a specific gene |
| `curated_blast_search` | genomeSearch.cgi | Find characterized proteins matching a functional description in a genome |
| `gapmind_check` | gapView.cgi | Check metabolic pathway completeness for an organism |
| `gapmind_list_organisms` | gapView.cgi (index mode) | List organisms available in GapMind |

Each tool takes structured input (Pydantic models with field descriptions, defaults, and validation) and returns structured JSON. This is the key design principle: **the MCP server does all the HTML wrangling so the LLM never has to**.

---

## 2. Project Initialization

### Starting from Templates

The workshop repository includes starter templates for both skills and MCP servers:

```
templates/
├── skill-template/
│   └── SKILL.md              ← Blank skill with section placeholders
└── mcp-template/
    ├── server.py             ← Minimal FastMCP server with one placeholder tool
    └── pyproject.toml        ← Python project metadata
```

To start a new skill+MCP project, copy both templates into the `examples/skills/` directory:

```bash
# From the workshop repo root
cp -r templates/skill-template examples/skills/my-skill
cp -r templates/mcp-template examples/skills/my-skill/scripts
```

The MCP template (`server.py`) gives you the minimal structure:

```python
from mcp.server.fastmcp import FastMCP

server = FastMCP("my-tools")

@server.tool()
def placeholder_tool(input_param: str) -> str:
    """Tool description."""
    return f"Result for: {input_param}"

if __name__ == "__main__":
    server.run()
```

### Discovering Your Configuration

Before building, you need to know where things live on your system:

```bash
# Where does Claude read skills from?
ls ~/.claude/skills/

# What MCP servers are already registered?
claude mcp list

# What Python are you using? (Must be 3.10+)
python3 --version

# Where will your MCP server run from?
which python3
```

The key paths are:

| What | Where |
|------|-------|
| Skills (SKILL.md + references) | `~/.claude/skills/<name>/` |
| MCP server code | `~/.claude/skills/<name>/scripts/` (or anywhere registered) |
| MCP registration | `~/.claude/settings.json` (managed by `claude mcp add`) |
| Workshop repo (canonical source) | `~/Claude/github-setup/ai-skills-workshop/` |

For detailed setup instructions see the [Workflow Guide](workflow-guide.md), Parts 1–4.

---

## 3. What Goes in the Skill vs. the MCP — and Why

The separation is simple in principle but subtle in practice.

**The MCP server** (`paperblast_mcp.py` + `models.py`) contains:

- HTTP request logic — fetching pages from papers.genomics.lbl.gov
- HTML parsers — BeautifulSoup-based extraction of structured data from CGI output
- Pydantic models — typed input validation and output serialization
- Tool definitions — the `@mcp.tool()` decorated functions that Claude can call
- Error handling — timeouts, connection errors, parser failures

**The SKILL.md** contains:

- Tool reference table — which tool to use when, with input/output summaries
- Workflow patterns — multi-step chains like "search → drill-down → synthesize"
- Query tips — what input formats work (identifiers vs. sequences vs. descriptions)
- Return data model descriptions — what fields mean and how to use them (e.g., `detail_id`)
- Caveats — HTML parsing fragility, network requirements

**Why this split matters:** The MCP server is executable code that runs as a subprocess. It cannot "teach" Claude anything — it only responds when called. The skill is text that Claude reads into context, providing the domain knowledge needed to *use* the tools correctly. Without the skill, Claude would not know to chain `paperblast_search` → `paperblast_gene_papers` using the `detail_id` field, or that `curated_blast_search` requires a `genome_id` to return useful results.

A practical heuristic: if removing a piece of information would cause Claude to use the tools incorrectly, it belongs in the SKILL.md. If removing it would cause the server to return wrong data, it belongs in the MCP code.

---

## 4. Designing the MCP

### 4.1 Architecture Overview

The PaperBLAST MCP uses a straightforward architecture:

```
Claude Code ←(stdio)→ FastMCP Server ←(HTTPS)→ papers.genomics.lbl.gov/cgi-bin/
                           │
                    ┌──────┴──────┐
                    │ paperblast_ │
                    │ mcp.py      │
                    │             │
                    │ _get()      │ → httpx async HTTP client
                    │ _parse_*()  │ → BeautifulSoup HTML parsers
                    │ models.py   │ → Pydantic input/output types
                    └─────────────┘
```

Key design decisions:

**Async HTTP with httpx.** The CGI endpoints can take 10–30 seconds for BLAST searches. We use `httpx.AsyncClient` with a 120-second timeout and automatic redirect following. A shared helper `_get(cgi_name, params)` handles all requests.

**BeautifulSoup + lxml for parsing.** The HTML output uses early-2000s patterns: `bgcolor` attributes, inline styles, `onmousedown` JavaScript handlers, and nested tables. We parse with BeautifulSoup using the `lxml` backend (faster than `html.parser`) and extract structured data using tag-attribute patterns, not CSS selectors.

**Pydantic models for input and output.** Every tool has a typed input model (with `Field` descriptions, defaults, and validation) and returns JSON serialized from a typed output model. This gives Claude explicit parameter documentation and ensures consistent output structure. The models live in a separate `models.py` file (13 models total) to keep the main server file focused on logic.

**FastMCP for server scaffolding.** We use the `FastMCP` class from the MCP Python SDK, which handles stdio transport, JSON-RPC framing, and tool registration. Each tool is a decorated async function:

```python
@mcp.tool(
    name="paperblast_search",
    annotations={
        "title": "PaperBLAST: Find Papers About a Protein",
        "readOnlyHint": True,
        "idempotentHint": True,
    },
)
async def paperblast_search(params: PaperBlastInput) -> str:
    ...
```

The `annotations` dict provides metadata: `readOnlyHint` tells Claude the tool doesn't modify anything, `idempotentHint` that it is safe to retry.

### 4.2 Discovering the API: Working Without Documentation

PaperBLAST has no formal API documentation. The "API" is whatever the CGI endpoints accept and return as HTML. Discovering the interface required three approaches.

**Reading the source code.** Morgan Price's PaperBLAST source is on [GitHub](https://github.com/morgannprice/PaperBLAST). The CGI scripts are Perl, and reading `litSearch.cgi`, `genomeSearch.cgi`, and `gapView.cgi` reveals the accepted URL parameters and the HTML generation logic. For example, `litSearch.cgi` accepts `query=` (sequence or identifier) and `more=` (bare accession for drill-down). The `genomeSearch.cgi` accepts `query=` (functional description), `gdb=` (genome database), and `gid=` (genome ID).

**Saving and inspecting HTML output.** We saved real HTML responses to analyze the structure:

```bash
curl -L 'https://papers.genomics.lbl.gov/cgi-bin/litSearch.cgi?query=P0AEZ3' \
  -o search_results.html
```

Then examined the HTML in a text editor to identify parsing patterns: which tags mark gene entries, where paper references are embedded, how the `more=` drill-down links are constructed. This is tedious but unavoidable when there is no API spec.

**Iterative testing.** We wrote parsers, tested them against saved HTML, found edge cases, and fixed them. The critical discovery was that different PaperBLAST endpoints use different HTML structures for similar data — the search results page uses `<p style="margin-top: 1em">` blocks with nested `<ul>` elements, while the `more=` page uses the same block structure but with a different header. Morgan's code reuses `PrintHits()` across pages, which is why the HTML is structurally similar but not identical.

### 4.3 Testing Before Installation

We tested at three levels before ever installing the skill:

**Level 1: Parser unit tests against saved HTML.**
Saved real HTML responses to files, then ran the parser functions against them in Python:

```python
from bs4 import BeautifulSoup
from paperblast_mcp import _parse_litsearch_results

with open("search_results.html") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

results = _parse_litsearch_results(soup)
print(f"Hits: {len(results.hits)}, Total found: {results.total_found}")
```

This catches parser bugs without network access and runs instantly.

**Level 2: Live connectivity test.**
The `check_deps.py` script verifies that all dependencies are installed and the server can reach papers.genomics.lbl.gov:

```bash
python3 scripts/check_deps.py --live
```

**Level 3: MCP schema validation.**
Running the server directly (`python3 paperblast_mcp.py`) starts it in stdio mode. The MCP inspector (`npx @anthropic-ai/mcp-inspector`) or a simple test client can list tools and validate input/output schemas before registering with Claude.

### 4.4 Design Decisions We Made — and Could Have Made Differently

**What we included:**

- `max_hits` parameter on `paperblast_search` (default 25) to control result size. Without this, a search returning 195 hits produces 14k+ tokens of JSON — overwhelming Claude's context.
- `detail_id` field on each search hit — the bare accession needed to drill down via `paperblast_gene_papers`. This was added after discovering that the `gene_entries[].gene_id` field uses a different ID format than the `more=` endpoint.
- `paper_source` field ("curated", "text_mining", "both") so Claude knows which hits will have drill-down papers available.
- `max_genome_hits` parameter on `curated_blast_search` (default 20) because the raw results page for "alcohol dehydrogenase in E. coli" contains 80 genome proteins × 25+ curated matches each = 2.4MB of HTML.

**What we could have done but didn't:**

- **Pagination.** When `total_found` is 195 and `max_hits` is 25, the remaining 170 hits are inaccessible. A `page` or `offset` parameter would let Claude request more results. We omitted this because in practice the top 25 hits (sorted by sequence similarity) cover the most relevant results, and pagination adds complexity.
- **Sequence input detection.** The tool accepts both identifiers (P0AEZ3) and raw sequences (MARIIVVTSG...). PaperBLAST handles this automatically, but we could pre-validate the input format and set appropriate timeouts (BLAST searches take 10–30s).
- **Caching.** Repeated searches for the same protein return the same results. An in-memory cache with a TTL would reduce server load. We omitted this for simplicity, since the MCP server restarts with each Claude Code session.
- **Structured paper metadata.** The `paper_snippets` field contains extracted text (year, title, journal) but not structured fields for each. A more complete implementation would parse into `{pmid, year, title, journal, authors}` objects.

---

## 5. Designing the Skill (SKILL.md)

The SKILL.md is what Claude reads to understand *how* to use the tools. It has three critical functions.

### Trigger Description (Frontmatter)

The `description` field in the YAML frontmatter determines when Claude activates the skill. It must be specific enough to trigger on relevant queries and broad enough to capture variations:

```yaml
description: >
  Search PaperBLAST for literature about proteins, find characterized proteins
  by function via Curated BLAST, and check metabolic pathway gaps with GapMind.
  Use when: (1) user asks about papers or literature for a protein or gene,
  (2) user wants to find characterized proteins matching a functional description,
  (3) user asks about amino acid biosynthesis or carbon source utilization
  capability of an organism, (4) user mentions PaperBLAST, GapMind, or Curated BLAST,
  (5) user wants to annotate hypothetical proteins using literature evidence.
```

The numbered trigger conditions are critical. Without them, Claude may not activate the skill when a user says "What papers are there about MinD?" because it does not know that this question maps to PaperBLAST.

### Tool Reference Table

A compact table mapping natural language use cases to tool names and inputs:

```
| Tool | Use when | Input | Returns |
|------|----------|-------|---------|
| paperblast_search | Finding papers about a protein | Sequence or ID + max_hits | PaperBlastResults |
| paperblast_gene_papers | Drilling into a specific hit | detail_id from prior search | GenePapersResults |
```

This table is the first thing Claude reads when deciding which tool to call. Keep it scannable.

### Workflow Patterns

Multi-step chains that Claude would not discover on its own:

**Pattern 1 (Annotate a protein):**
1. `paperblast_search` → get hits with identity% and `detail_id`
2. `paperblast_gene_papers(gene_id=detail_id)` → get full paper list

The critical instruction here is "use `detail_id` — not `gene_entries[].gene_id`." Without this, Claude will try the gene_id (which uses a different format) and get zero results. We learned this the hard way during testing (see Section 7).

**Pattern 3 (Predict metabolism):**
1. `gapmind_list_organisms` → check if organism is available
2. `gapmind_check(organism="Pseudomonas fluorescens")` → get pathway predictions

The key insight for users: GapMind only works on pre-computed organisms. If your organism is not in the list, you cannot use this tool.

### Data Model Descriptions

The return data models section explains what each field means. This is especially important for fields that control downstream behavior:

- `detail_id`: "bare accession to pass to `paperblast_gene_papers`. Empty for hits with few papers. **Use this — not gene_entries[].gene_id — as the gene_id argument.**"
- `paper_source`: "curated", "text_mining", or "both" — tells Claude whether drill-down will work

---

## 6. Installation

Installation involves three steps: dependencies, file placement, and MCP registration.

### Dependencies

```bash
pip install httpx beautifulsoup4 lxml pydantic "mcp[cli]"
```

### File Placement

Skills live in `~/.claude/skills/<name>/`. The directory structure:

```
~/.claude/skills/paperblast/
├── SKILL.md
└── scripts/
    ├── paperblast_mcp.py
    └── models.py
```

Copy from the repo:

```bash
mkdir -p ~/.claude/skills/paperblast/scripts
cp examples/skills/02-paperblast/SKILL.md ~/.claude/skills/paperblast/
cp examples/skills/02-paperblast/scripts/paperblast_mcp.py ~/.claude/skills/paperblast/scripts/
cp examples/skills/02-paperblast/scripts/models.py ~/.claude/skills/paperblast/scripts/
```

### MCP Registration

```bash
claude mcp add --scope user paperblast \
  python3 \
  ~/.claude/skills/paperblast/scripts/paperblast_mcp.py
```

The `--scope user` flag makes the server available in all projects. After registration, verify with `claude mcp list` and restart Claude Code.

For full details, see [INSTALL.md](../examples/skills/02-paperblast/INSTALL.md).

---

## 7. Testing

### 7.1 Test Commands and Expected Outcomes

After installation and Claude Code restart, run these tests in order:

**Test 1: Basic search**

```
Search PaperBLAST for P0AEZ3
```

Expected: The `paperblast_search` tool is called with `{"query": "P0AEZ3"}`. Returns ~25 hits (of 195 total) with gene entries, paper snippets, and identity percentages. The top hit should be MinD / b1175 at 100% identity with 98 curated papers.

**Test 2: Gene paper drill-down (chain test)**

```
Get the full paper list for the top hit from the P0AEZ3 search using its detail_id
```

Expected: Claude reads the `detail_id` ("P0AEZ3") from the search results and calls `paperblast_gene_papers(gene_id="P0AEZ3")`. Returns 147 papers (98 curated + 49 text-mined) with gene entries from EcoCyc, SwissProt, RefSeq, and MicrobesOnline.

**Test 3: Curated BLAST**

```
Use Curated BLAST to find characterized alcohol dehydrogenases in E. coli K-12 (genome GCF_000005845.2)
```

Expected: `curated_blast_search` is called with the query and genome ID. Returns 20 of 79 genome proteins, each with its best characterized match. Top hits include adhE, adhP, frmA, yqhD, and ahr.

If called without a genome_id, the tool should return a warning: "Curated BLAST returned the genome-selection form — no results. You must specify genome_id."

**Test 4: GapMind organism list**

```
List organisms available in GapMind for amino acid biosynthesis
```

Expected: `gapmind_list_organisms` (or `gapmind_check` with no organism) returns a list of ~206 organisms with their `org_id` values.

**Test 5: GapMind pathway check**

```
Check amino acid biosynthesis gaps in Pseudomonas fluorescens using GapMind
```

Expected: `gapmind_check` is called. Returns 18 pathways: 16 high-confidence, 1 medium (methionine), 1 low (histidine — a likely false gap at the `prs` step).

### 7.2 Working with Returned JSON

The MCP tools return structured JSON conforming to Pydantic models. This enables programmatic use beyond just reading the results.

**Saving raw JSON output.** When Claude displays results, ask it to save the raw JSON:

```
Save the raw JSON from that search to paperblast_results.json
```

**Extracting to TSV/CSV.** Ask Claude to transform structured results:

```
Extract all hits from the P0AEZ3 search into a TSV with columns:
gene_name, organism, identity, coverage, paper_source, detail_id
```

Claude can use the structured JSON fields directly — no regex or HTML parsing needed, because the MCP server already did that work.

**Filtering results.** Because the output is structured, Claude can filter without re-querying:

```
From those results, show only hits with identity > 80% that have paper_source="both"
```

### 7.3 Bugs We Found During Testing

Development was not linear. Here are the real bugs we encountered and how we diagnosed them:

**Bug 1: gene_papers returned 0 results for all ID formats.**
When we first tested the chain (search → gene_papers), Claude tried six different gene_id formats: `MIND_ECOLI / P0AEZ3`, `b1175`, `MinB / b1175`, `SwissProt::P0AEZ3`, `UTI89_C1360`, `NP_415693`. All returned zero results. The `more=` endpoint requires bare accessions like `P0AEZ3`, not locus tags or database-prefixed IDs.

Diagnosis: We saved the search results HTML and examined the `more=` links — they all used bare accessions. We then saved the `more=P0AEZ3` page and confirmed the existing parser could handle it.

Fix: Added `detail_id` field (extracted from `more=` links in search results, with UniProt accession fallback), and added ID cleanup in `gene_papers` to strip `" / "` prefixes and `"::"` prefixes.

**Bug 2: curated_blast_search returned form text as results.**
When called without a `genome_id`, the CGI returns its genome-selection form page. The parser's paragraph-scanning strategy picked up form text ("Or upload a genome or proteome in fasta format") as results, returning 5 spurious matches.

Diagnosis: We saved both the form page HTML and a real results page. The form page has `<select name="gdb">` but no `bgcolor` rows; the results page has `bgcolor` rows but no genome selector.

Fix: Added upfront form-page detection: if `<select name="gdb">` exists and no `bgcolor` rows exist, return a warning instead of trying to parse.

**Bug 3: curated_blast_search overflowed MCP response limit.**
With a genome specified, "alcohol dehydrogenase" in E. coli returned 80 genome proteins × 25+ curated matches each = 2003 total rows = 2.4MB of JSON. This exceeded Claude Code's MCP response size limit.

Diagnosis: We inspected the HTML structure and found each `<table>` represents one genome protein, with row 0 being the genome protein header and rows 1+ being characterized protein matches.

Fix: Restructured the parser to return one entry per genome protein (with its best curated match only), capped at `max_genome_hits=20`. Output went from 2.4MB to 17.7KB.

---

## 8. Repository Workflow and Team Collaboration

### Pushing a New Skill to the Repository

The workshop repository uses a standard Git workflow. Your skill has two locations:

1. **Canonical source** (in the repo): `examples/skills/02-paperblast/`
2. **Installed skill** (on your machine): `~/.claude/skills/paperblast/`

You develop and test with the installed copy, then sync to the canonical source for commits:

```bash
# After testing confirms the installed skill works:
cp ~/.claude/skills/paperblast/scripts/paperblast_mcp.py \
   examples/skills/02-paperblast/scripts/paperblast_mcp.py
cp ~/.claude/skills/paperblast/scripts/models.py \
   examples/skills/02-paperblast/scripts/models.py
cp ~/.claude/skills/paperblast/SKILL.md \
   examples/skills/02-paperblast/SKILL.md

# Commit
git add examples/skills/02-paperblast/
git commit -m "Update PaperBLAST skill: add detail_id, fix curated_blast parser"
git push
```

### Updating an Existing Skill

When pulling updates from the repo:

```bash
git pull

# Re-deploy to installed location
cp examples/skills/02-paperblast/scripts/paperblast_mcp.py \
   ~/.claude/skills/paperblast/scripts/
cp examples/skills/02-paperblast/scripts/models.py \
   ~/.claude/skills/paperblast/scripts/
cp examples/skills/02-paperblast/SKILL.md \
   ~/.claude/skills/paperblast/
```

The MCP registration persists — no need to re-run `claude mcp add`. But you must restart Claude Code to pick up new server code.

### Working as a Team

When multiple people are developing the same skill:

**Coordinate on the interface, not the implementation.** Agree on tool names, input parameters, and output model fields. These are the API surface that the SKILL.md references. The parser implementation behind each tool can be changed independently.

**Use the models.py as a contract.** The Pydantic models define what the tools return. If someone adds a field to `PaperBlastHit`, the SKILL.md needs updating, and everyone's installed copy needs refreshing.

**Branch per feature.** Use feature branches for non-trivial changes. A branch that adds a new tool is easy to review; a branch that rewrites the parser for an existing tool needs testing against saved HTML to verify it still produces the same output.

**Share saved HTML test files.** Parser bugs are diagnosed by running parsers against saved HTML. Keep a `test_data/` directory (gitignored if large) with representative HTML pages for each endpoint variant. When someone reports a parser bug, ask them to save the HTML: `curl -L 'https://papers.genomics.lbl.gov/cgi-bin/litSearch.cgi?query=P0AEZ3' -o test_data/search_P0AEZ3.html`.

**The canonical source is what gets committed.** The installed skill is your local working copy. Always sync installed → canonical before committing, and canonical → installed after pulling.

For complete contribution instructions, see the [Workflow Guide](workflow-guide.md), Part 6.

---

## 9. What Would Improve the PaperBLAST Skill?

These are concrete improvements the team could implement. They are ordered by estimated impact and difficulty.

### Quick Wins

**Reduce default `max_hits` from 25 to 10.** The current default produces ~14k tokens of JSON, which triggers Claude Code's "Large MCP response" warning. Reducing to 10 hits would cut this to ~6k tokens while still covering the most relevant results. Users can override with `max_hits=25` when needed.

**Add `paper_count` to each hit.** Currently, Claude must count `paper_snippets` to know how many papers a hit has. Adding a `total_papers` integer field would make filtering ("show only hits with >5 papers") trivial.

**Improve `gapmind_check` organism matching.** The current fuzzy matching against the organism index sometimes fails on common name variants. Adding a few more aliases (e.g., "E. coli" → "Escherichia coli") would reduce the need for users to look up exact names.

### Medium Effort

**Pagination for `paperblast_search`.** Add `offset` parameter so Claude can request results 26–50, 51–75, etc. This enables: "Show me the next 25 hits" after an initial search.

**Structured paper metadata.** Parse `paper_snippets` into typed objects: `{pmid, year, title, journal, first_author, excerpt}`. Currently the snippet is a single text string. Structured fields enable: "List all papers from 2020 or later about MinD."

**GapMind step-level detail.** The current output shows pathway-level confidence. Adding per-step information (which gene was matched, at what confidence) would let Claude explain *why* a pathway has a gap — not just that it does.

### Larger Projects

**Wrap `curatedClusters.cgi`.** PaperBLAST also has a Curated Clusters tool that shows functional families of characterized proteins. This would complement Curated BLAST by letting users explore protein families.

**Add sequence-to-structure via PDB links.** Many PaperBLAST hits include PDB structural references. Extracting these and linking to structure viewers would add a structural biology dimension to the skill.

**Upload genome mode for Curated BLAST.** The current tool only supports pre-indexed genomes (NCBI, IMG, etc.). Curated BLAST also accepts uploaded FASTA proteomes. Supporting this would require multipart form submission and longer timeouts but would dramatically expand the set of searchable genomes.

**Build a test suite with saved HTML fixtures.** Create a `test_data/` directory with representative HTML files for each endpoint and a pytest suite that validates parser output against known-good results. This would catch parser regressions when PaperBLAST's HTML format changes.

---

## Appendix: File Inventory

```
examples/skills/02-paperblast/
├── SKILL.md              ← Workflow guidance Claude reads at runtime
├── INSTALL.md            ← Step-by-step installation for users
├── TESTING.md            ← How to run and interpret parser tests
├── USAGE-EXAMPLES.md     ← Worked examples with real output
├── README.md             ← Skill overview and what it teaches
├── pyproject.toml        ← Python dependencies
├── references/
│   └── setup.md          ← Extended setup notes and future tools
└── scripts/
    ├── paperblast_mcp.py ← MCP server (5 tools + HTML parsers, ~1200 lines)
    ├── models.py         ← Pydantic output models (13 models, ~440 lines)
    ├── test_parser.py    ← Live parser tests
    └── check_deps.py     ← Dependency diagnostic
```

Companion documentation in `docs/`:

- [developing-paperblast-skill.md](developing-paperblast-skill.md) — This file
- [paperblast-skill-design.md](paperblast-skill-design.md) — Retrospective design analysis
- [skill-authoring-guide.md](skill-authoring-guide.md) — General skill writing guide
- [workflow-guide.md](workflow-guide.md) — Setup, registration, contribution workflow
