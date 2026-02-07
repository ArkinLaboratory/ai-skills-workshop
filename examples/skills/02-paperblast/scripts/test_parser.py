#!/usr/bin/env python3
"""
Live parser test — runs P0AEZ3 query against papers.genomics.lbl.gov
and validates the parsed output.

Requires: VPN connection to LBL network.
Usage:    python3 test_parser.py
"""
import asyncio
import json
import sys
import os

# Add script dir to path so we can import the server module
sys.path.insert(0, os.path.dirname(__file__))

from paperblast_mcp import _get, _parse_litsearch_results

async def main():
    print("Fetching P0AEZ3 from PaperBLAST...")
    try:
        soup = await _get("litSearch.cgi", {"query": "P0AEZ3"})
    except Exception as e:
        print(f"FAIL: Could not reach PaperBLAST: {e}")
        print("Are you on LBL VPN?")
        sys.exit(1)

    print("Parsing HTML...")
    results = _parse_litsearch_results(soup)

    # --- Validate structure ---
    errors = []

    qi = results.get("query_info", "")
    if "MinD" not in qi and "P0AEZ3" not in qi:
        errors.append(f"query_info missing MinD/P0AEZ3: got '{qi[:80]}'")
    else:
        print(f"  OK  query_info: {qi[:100]}")

    tf = results.get("total_found", 0)
    if tf < 50:
        errors.append(f"total_found too low: {tf} (expected >100)")
    else:
        print(f"  OK  total_found: {tf}")

    hits = results.get("hits", [])
    if len(hits) < 5:
        errors.append(f"Only {len(hits)} hits parsed (expected many)")
    else:
        print(f"  OK  parsed {len(hits)} hits")

    # Check first hit (should be E. coli MinD, 100% identity)
    if hits:
        h0 = hits[0]
        if h0.get("identity") != "100%":
            errors.append(f"First hit identity: '{h0.get('identity')}' (expected '100%')")
        else:
            print(f"  OK  first hit identity: {h0['identity']}")

        if h0.get("coverage") != "100%":
            errors.append(f"First hit coverage: '{h0.get('coverage')}' (expected '100%')")
        else:
            print(f"  OK  first hit coverage: {h0['coverage']}")

        ge = h0.get("gene_entries", [])
        if not ge:
            errors.append("First hit has no gene_entries")
        else:
            print(f"  OK  first hit gene_entries: {len(ge)}")
            g0 = ge[0]
            print(f"      primary: {g0.get('name')} | {g0.get('db')} | {g0.get('description')[:60]}")
            print(f"      organism: {g0.get('organism')}")

        tp = h0.get("total_curated_papers", 0)
        if tp < 10:
            errors.append(f"First hit total_curated_papers: {tp} (expected many)")
        else:
            print(f"  OK  first hit curated papers: {tp}")

        func = h0.get("function", "")
        if not func:
            errors.append("First hit missing function annotation")
        else:
            print(f"  OK  function: {func[:80]}...")

    # Check for any hit with paper_snippets (text-mined papers)
    snippets_found = sum(len(h.get("paper_snippets", [])) for h in hits)
    if snippets_found == 0:
        errors.append("No text-mined paper_snippets found in any hit")
    else:
        print(f"  OK  total paper_snippets across all hits: {snippets_found}")
        # Show first snippet
        for h in hits:
            if h.get("paper_snippets"):
                s = h["paper_snippets"][0]
                print(f"      example: {s.get('title', '')[:70]}")
                print(f"      citation: {s.get('citation', '')[:60]}")
                if s.get("excerpt"):
                    print(f"      excerpt: {s['excerpt'][:80]}...")
                break

    # --- Summary ---
    print()
    if errors:
        print(f"FAILED: {len(errors)} issue(s):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("ALL PARSER TESTS PASSED.")
        # Dump first 2 hits as JSON sample
        print("\n--- Sample output (first 2 hits) ---")
        sample = {k: v for k, v in results.items() if k != "hits"}
        sample["hits"] = hits[:2]
        print(json.dumps(sample, indent=2, ensure_ascii=False))
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
