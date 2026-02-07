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

This skill provides four tools via the `paperblast_mcp` MCP server:

| Tool | Use when | Input |
|------|----------|-------|
| `paperblast_search` | Finding papers about a protein | Sequence or identifier |
| `paperblast_gene_papers` | Drilling into a specific hit | Gene ID from prior search |
| `curated_blast_search` | Finding characterized proteins by function | Functional description + optional genome |
| `gapmind_check` | Checking metabolic completeness | Analysis type (aa/carbon) + organism |

## Workflow Patterns

### Pattern 1: Annotate a hypothetical protein

1. `paperblast_search` with the protein sequence
2. Review hits — check identity % and paper relevance
3. For promising hits, `paperblast_gene_papers` to get the full literature
4. Synthesize annotation from convergent evidence

### Pattern 2: Find functional homologs in a genome

1. `curated_blast_search` with a functional description (e.g., "acetaldehyde dehydrogenase")
2. Optionally specify genome_db="NCBI" and genome_id for a specific organism
3. Results show experimentally-characterized proteins with homologs in the target genome

### Pattern 3: Predict metabolic capability

1. `gapmind_check` with analysis_type="aa" for amino acid biosynthesis
2. `gapmind_check` with analysis_type="carbon" for carbon catabolism
3. High-confidence = pathway complete; low = missing steps (gaps)

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
- **GapMind organism names** should match NCBI taxonomy or genome identifiers

## HTML Parsing Note

These tools scrape HTML from CGI endpoints (no formal JSON API exists). The
HTML parsers in `scripts/paperblast_mcp.py` use heuristic pattern matching
and may need updates if the page structure changes. If results look wrong,
check the `search_url` or `detail_url` field in the output to verify against
the live web page.

## Setup

See [references/setup.md](references/setup.md) for installation and configuration.
