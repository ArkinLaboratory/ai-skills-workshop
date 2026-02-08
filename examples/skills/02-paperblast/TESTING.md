# PaperBLAST MCP — Testing Guide

## Prerequisites

All live tests require **LBL VPN** (Cloudflare blocks non-LBL IPs). See [LBNL VPN setup](https://commons.lbl.gov/spaces/itfaq/pages/132810873/VPN+Information).

```bash
cd ~/Claude/paperblast-skill/scripts
```

## Test Commands

```bash
# Schema validation only (no network)
python3 test_parser.py --schema

# PaperBLAST parser test (default)
python3 test_parser.py

# GapMind tests (index + organism results)
python3 test_parser.py --gapmind

# Curated BLAST test
python3 test_parser.py --curated

# All tests
python3 test_parser.py --all

# Dump JSON schemas for all output models
python3 test_parser.py --schema-dump
```

## What Each Test Validates

### Schema test (offline)
- All 5 output models (`PaperBlastResults`, `GenePapersResults`,
  `CuratedBlastResults`, `GapMindResults`, `GapMindOrganismIndex`)
  produce valid JSON Schema with expected properties.

### PaperBLAST test
- Query: `P0AEZ3` (E. coli MinD, 270 aa)
- Validates: `PaperBlastResults` model, ≥50 hits, first hit = 100% identity/coverage,
  gene entries with `GeneEntry` model, function annotation, ≥1 text-mined paper snippet
- JSON round-trip: serialize → deserialize → compare

### GapMind index test
- Fetches organism index for amino acid biosynthesis (`set=aa&orgs=orgsDef`)
- Validates: `_parse_organism_index()` returns ≥20 `GapMindOrganism` entries,
  FitnessBrowser organisms present, fuzzy matching works for "Pseudomonas"

### GapMind results test
- Fetches results for first organism in index (`orgId` from index)
- Validates: `GapMindResults` model, ≥1 pathway, confidence values (high/medium/low),
  JSON round-trip

### Curated BLAST test
- Query: "alcohol dehydrogenase"
- Validates: `CuratedBlastResults` model, ≥1 match, JSON round-trip

## Known-Good Reference (P0AEZ3)

```
query_info: "P0AEZ3 MinD ... (Escherichia coli K-12) (270 a.a.)"
total_found: ~195+
hits[0].identity: "100%"
hits[0].coverage: "100%"
hits[0].gene_entries[0].name: contains "MinD"
hits[0].function: contains "Septum site-determining protein MinD"
total paper_snippets: ~438+
```

## Testing the MCP Tools End-to-End

In Claude Code (with VPN active):

```
# Test PaperBLAST
> Use paperblast_search for P0AEZ3

# Test GapMind (should NOT return 500 anymore)
> Use gapmind_list_organisms for amino acid biosynthesis
> Use gapmind_check for Pseudomonas fluorescens amino acid biosynthesis

# Test Curated BLAST
> Use curated_blast_search for "alcohol dehydrogenase"
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `httpx.ConnectError` | Not on VPN | Connect to LBL VPN |
| `HTTP 403` | Cloudflare blocking | VPN required |
| `HTTP 500` from gapmind_check | Wrong CGI params | Use org_id or organism name (v2 fixes this) |
| `0 organisms parsed` | Index page HTML changed | Check `gapView.cgi?set=aa&orgs=orgsDef` in browser |
