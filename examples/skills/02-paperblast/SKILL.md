---
name: paperblast
description: >
  Search PaperBLAST for literature about proteins, find characterized proteins
  by function via Curated BLAST, and check metabolic pathway gaps with GapMind.
  Use when: (1) user asks about papers or literature for a protein or gene,
  (2) user wants to find characterized proteins matching a functional description,
  (3) user asks about amino acid biosynthesis or carbon source utilization
  capability of an organism, (4) user mentions PaperBLAST, GapMind, or Curated BLAST,
  (5) user wants to annotate hypothetical proteins using literature evidence.
  Wraps papers.genomics.lbl.gov CGI tools via MCP server.
---

# PaperBLAST Skill

## Available MCP Tools

This skill provides five tools via the `paperblast_mcp` MCP server.
All tools return **structured JSON** matching Pydantic output models
(defined in `scripts/models.py`), enabling programmatic filtering,
sorting, and pipeline integration.

| Tool | Use when | Input | Returns |
|------|----------|-------|---------|
| `paperblast_search` | Finding papers about a protein | Sequence or identifier + `max_hits` (default 25) | `PaperBlastResults` |
| `paperblast_gene_papers` | Drilling into a specific hit | `detail_id` from prior search hit (bare accession) | `GenePapersResults` |
| `curated_blast_search` | Finding characterized proteins by function | Functional description + optional genome | `CuratedBlastResults` |
| `gapmind_check` | Checking metabolic completeness | Analysis type (aa/carbon) + organism or org_id | `GapMindResults` or `GapMindOrganismIndex` |
| `gapmind_list_organisms` | Listing available GapMind organisms | Analysis type (aa/carbon) | `GapMindOrganismIndex` |

## Return Data Models

All tools return JSON conforming to typed Pydantic models. Key structures:

**PaperBlastResults** — hits ordered by sequence similarity (capped at `max_hits`, default 25), each containing:
- `gene_entries`: curated database entries (name, db, description, organism, gene_id)
- `identity`, `coverage`: sequence similarity metrics
- `function`, `subunit`: experimentally characterized annotations
- `paper_snippets`: text-mined paper references with excerpts
- `paper_source`: "curated", "text_mining", or "both" — indicates whether
  `paperblast_gene_papers` will return results for this hit
- `detail_id`: bare accession to pass to `paperblast_gene_papers` (e.g. "P0AEZ3").
  Empty for hits with few papers. **Use this — not gene_entries[].gene_id — as the
  gene_id argument to gene_papers.**

**GapMindResults** — pathway completeness for an organism:
- `pathways`: each with `name`, `confidence` (high/medium/low), `status`, `url`
- `org_id`: the GapMind organism identifier used

**GapMindOrganismIndex** — list of organisms available in GapMind:
- `organisms`: each with `org_id` (for direct lookup), `name`

This structured output enables queries like "show only medium-confidence pathways"
or "list all hits with >80% identity" without re-parsing raw text.

## Workflow Patterns

### Pattern 1: Annotate a hypothetical protein

1. `paperblast_search` with the protein sequence
2. Review hits — check identity %, paper relevance, `paper_source`, and `detail_id`
3. For hits with non-empty `detail_id`, use `paperblast_gene_papers(gene_id=detail_id)`
   to get the full literature. Hits with `paper_source='text_mining'` or empty
   `detail_id` won't have drill-down papers.
4. Synthesize annotation from convergent evidence

### Pattern 2: Find functional homologs in a genome

1. `curated_blast_search` with a functional description (e.g., "acetaldehyde dehydrogenase")
2. Optionally specify genome_db="NCBI" and genome_id for a specific organism
3. Results show experimentally-characterized proteins with homologs in the target genome

### Pattern 3: Predict metabolic capability

GapMind only has results for **pre-computed organisms**. Use the two-step flow:

1. `gapmind_list_organisms` (or `gapmind_check` with no organism) to browse available organisms
2. `gapmind_check` with `organism="Pseudomonas fluorescens"` — fuzzy-matches against the index
3. Or use `org_id` directly if you already know it: `gapmind_check(org_id="FitnessBrowser__pseudo1_N1B4")`
4. High-confidence = pathway complete; low = missing steps (gaps)

### Pattern 4: Cross-tool enrichment (PROTECT example)

1. Get organism list from KBase metagenome analysis
2. For each organism of interest, `gapmind_check` to predict metabolism
3. For key proteins, `paperblast_search` to find literature evidence
4. `curated_blast_search` to identify characterized homologs

## Query Tips

- **Protein identifiers** work better than sequences for quick lookups:
  UniProt (P0AEZ3), RefSeq (WP_003246543.1), VIMSS locus tags (VIMSS14484)
- **Raw sequences** trigger a BLAST search (slower, ~10-30s) but work for
  novel proteins with no known identifier
- **Curated BLAST queries** should be functional descriptions, not gene names.
  Good: "alcohol dehydrogenase", "two-component sensor kinase"
  Bad: "acrB", "SO_1234"
- **GapMind organisms** are fuzzy-matched against a pre-computed index.
  Not all organisms are available — use `gapmind_list_organisms` to check.
  If fuzzy matching fails, the tool returns the organism index with suggestions.

## HTML Parsing Note

These tools scrape HTML from CGI endpoints (no formal JSON API exists). The
HTML parsers in `scripts/paperblast_mcp.py` use heuristic pattern matching
and may need updates if the page structure changes. If results look wrong,
check the `search_url`, `detail_url`, or `gapmind_url` field in the output
to verify against the live web page.

> **Network requirement:** All tools query papers.genomics.lbl.gov, which requires LBNL VPN access.

## Project Structure

```
paperblast-skill/
├── SKILL.md              ← This file (workflow guidance for Claude)
├── TESTING.md            ← Test documentation
├── pyproject.toml        ← Dependencies
└── scripts/
    ├── paperblast_mcp.py ← MCP server (tools + parsers)
    ├── models.py         ← Pydantic output models
    ├── test_parser.py    ← Live parser tests
    └── check_deps.py     ← Dependency checker
```

## Setup

See [INSTALL.md](INSTALL.md) for step-by-step installation.
See [references/setup.md](references/setup.md) for extended notes (transport modes, extending to new tools).
