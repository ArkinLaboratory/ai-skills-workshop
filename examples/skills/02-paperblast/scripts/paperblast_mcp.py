#!/usr/bin/env python3
"""
MCP Server for PaperBLAST and related Arkin Lab genomics tools.

Wraps the CGI interfaces at papers.genomics.lbl.gov with typed MCP tools,
parsing HTML responses into structured data suitable for agentic workflows.

Tools:
  - paperblast_search: Search for papers about a protein by sequence or identifier
  - paperblast_gene_papers: Get full paper list for a specific gene
  - curated_blast_search: Search for characterized proteins matching a description
  - gapmind_check: Check amino acid or carbon source biosynthesis gaps in a genome

Requires: httpx, beautifulsoup4, lxml, pydantic, mcp
Install:  pip install httpx beautifulsoup4 lxml "mcp[cli]"
Run:      python paperblast_mcp.py           (stdio transport, for local use)
          python paperblast_mcp.py --http    (HTTP transport, for remote/shared)
"""

import json
import logging
import re
import sys
from enum import Enum
from typing import Optional, List, Dict, Any

# ---------------------------------------------------------------------------
# Startup guard — catch import errors gracefully so Claude Code doesn't hang
# ---------------------------------------------------------------------------
_MISSING: List[str] = []

try:
    import httpx
except ImportError:
    _MISSING.append("httpx")

try:
    from bs4 import BeautifulSoup, Tag
except ImportError:
    _MISSING.append("beautifulsoup4")

try:
    import lxml  # noqa: F401 — needed by BeautifulSoup
except ImportError:
    _MISSING.append("lxml")

try:
    from pydantic import BaseModel, Field, field_validator, ConfigDict
except ImportError:
    _MISSING.append("pydantic")

# Import after pydantic is verified available
import difflib

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    _MISSING.append("mcp[cli]")

if _MISSING:
    print(
        f"PaperBLAST MCP server: missing dependencies: {', '.join(_MISSING)}\n"
        f"Install with: pip install {' '.join(_MISSING)}",
        file=sys.stderr,
    )
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s: %(message)s")
log = logging.getLogger("paperblast_mcp")

# Output models — separated for teaching clarity (input vs output vs logic)
from models import (
    PaperRef, ProteinLink, GeneEntry, PaperBlastHit, PaperBlastResults,
    GenePapersResults, CuratedMatch, CuratedBlastResults,
    GapMindOrganism, GapMindStep, GapMindPathway, GapMindResults,
    GapMindOrganismIndex,
)

# ---------------------------------------------------------------------------
# Server setup
# ---------------------------------------------------------------------------
mcp = FastMCP("paperblast_mcp")

BASE_URL = "https://papers.genomics.lbl.gov"
CGI = f"{BASE_URL}/cgi-bin"
TIMEOUT = 60.0  # BLAST searches can be slow

# ---------------------------------------------------------------------------
# Shared HTTP helpers
# ---------------------------------------------------------------------------

async def _get(endpoint: str, params: Dict[str, str]) -> BeautifulSoup:
    """Make GET request to CGI endpoint, return parsed HTML."""
    async with httpx.AsyncClient(
        timeout=TIMEOUT,
        follow_redirects=True,
        headers={"User-Agent": "PaperBLAST-MCP/1.0 (Arkin Lab agent skill)"}
    ) as client:
        resp = await client.get(f"{CGI}/{endpoint}", params=params)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")


def _handle_error(e: Exception) -> str:
    """Consistent error formatting."""
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        if status == 404:
            return "Error: Endpoint not found. The PaperBLAST server may be down."
        if status == 500:
            return "Error: PaperBLAST server error. The query may be malformed or the server is overloaded."
        return f"Error: HTTP {status} from PaperBLAST server."
    if isinstance(e, httpx.TimeoutException):
        return "Error: Request timed out. BLAST searches on long sequences can take >30s. Try a shorter sequence or an identifier."
    return f"Error: {type(e).__name__}: {e}"


def _clean_text(tag: Tag) -> str:
    """Extract clean text from an HTML tag, collapsing whitespace."""
    if tag is None:
        return ""
    return re.sub(r'\s+', ' ', tag.get_text(separator=' ')).strip()


def _extract_links(tag: Tag, base: str = BASE_URL) -> List[Dict[str, str]]:
    """Extract all hyperlinks from a tag as [{text, href}]."""
    links = []
    if tag is None:
        return links
    for a in tag.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/"):
            href = base + href
        links.append({"text": _clean_text(a), "href": href})
    return links

# ---------------------------------------------------------------------------
# HTML parsers — one per tool, isolating fragile scraping logic
# ---------------------------------------------------------------------------
# Reverse-engineered from live litSearch.cgi output (Feb 2026).
#
# Real HTML structure:
#   <h3>PaperBLAST Hits for {ACCESSION} {NAME} ({ORG}) ({LEN} a.a., {SEQ}...)</h3>
#   <DIV style="float:right ..."> sidebar with cross-tool links </DIV>
#   <p>Found {N} similar proteins in the literature:</p>
#   For each hit:
#     <p style="margin-top: 1em; margin-bottom: 0em;">
#       <a onmousedown="logger(this,'curated::GENE_ID')" title="DB">NAME</a>
#       <b>description</b> from <i>organism</i>
#       (see <a onmousedown="logger(this,'curatedpaper::GENE_ID')">N papers</a>)
#       <BR> ... more db entries for same protein ...
#       <a style="font-family: sans-serif; font-size: smaller;"
#          title="alignment detail">N% identity, M% coverage</a>
#       <UL><LI><b>function:</b> text
#            <LI><b>subunit:</b> text</UL>
#       OR for text-mined hits:
#       <UL><LI>
#         <a onmousedown="logger(this,'pb::GENE')">Paper title</a>
#         <br/><small>Author, Journal Year</small>
#         <UL><LI>"...snippet with <B><span style="color:red;">term</span></B>..."</UL>
#       </LI></UL>
#     </p>

def _parse_litsearch_results(soup: BeautifulSoup) -> PaperBlastResults:
    """Parse litSearch.cgi HTML into structured PaperBlastResults."""
    query_info = ""
    total_found = 0
    warnings: List[str] = []
    hits: List[PaperBlastHit] = []

    # --- Header ---
    h3 = soup.find("h3")
    if h3:
        query_info = _clean_text(h3)

    # --- Total count ---
    for p in soup.find_all("p"):
        m = re.search(r"Found\s+(\d+)\s+similar\s+proteins?", _clean_text(p))
        if m:
            total_found = int(m.group(1))
            break

    # --- Warnings / errors ---
    for p in soup.find_all("p"):
        text = _clean_text(p)
        if re.search(r"\b(sorry|error|no results|no hits|not found)\b", text, re.I):
            warnings.append(text)

    # --- Hit blocks: <p style="margin-top: 1em ..."> ---
    # IMPORTANT: lxml auto-closes <p> when it encounters block-level <UL>.
    # In Morgan's HTML the <UL> with function/subunit/snippets is written
    # inside the <p>, but lxml parses it as a SIBLING.  So we must collect
    # trailing <UL> siblings that belong to each hit <p>.
    hit_blocks = soup.find_all("p", style=re.compile(r"margin-top:\s*1em"))

    for block in hit_blocks:
        trailing_uls: List[Tag] = []
        sib = block.next_sibling
        while sib is not None:
            if isinstance(sib, Tag):
                if sib.name == "p":
                    break
                if sib.name == "ul":
                    trailing_uls.append(sib)
            sib = sib.next_sibling

        hit = _parse_hit_block(block, trailing_uls)
        if hit:
            hits.append(hit)

    return PaperBlastResults(
        query_info=query_info,
        total_found=total_found,
        hits=hits,
        warnings=warnings,
    )


def _parse_hit_block(block: Tag, trailing_uls: List[Tag] = None) -> Optional[PaperBlastHit]:
    """Parse a single PaperBLAST hit <p> block + trailing <UL> siblings."""
    if trailing_uls is None:
        trailing_uls = []
    # Accumulate raw data, then construct the Pydantic model at the end
    gene_entries: List[GeneEntry] = []
    identity = ""
    coverage = ""
    function_text = ""
    subunit_text = ""
    paper_snippets: List[PaperRef] = []
    total_curated_papers = 0
    detail_id = ""

    # --- Gene entries: <a> with onmousedown containing "curated::" ---
    for a in block.find_all("a", attrs={"onmousedown": re.compile(r"curated::")}):
        md = re.search(r"curated::(.+?)(?:'|\")", a.get("onmousedown", ""))
        gene_id = md.group(1).strip() if md else _clean_text(a)

        entry_name = _clean_text(a)
        entry_db = a.get("title", "")
        entry_desc = ""
        entry_org = ""

        # Description: <b> tag that is a next sibling of this <a>
        sib = a.next_sibling
        while sib is not None:
            if isinstance(sib, Tag):
                if sib.name == "b":
                    entry_desc = _clean_text(sib)
                    break
                if sib.name in ("br", "a", "ul", "p"):
                    break
            sib = getattr(sib, "next_sibling", None)

        # Organism: first <i> after this <a>, before next <BR> or <a>
        sib = a.next_sibling
        while sib is not None:
            if isinstance(sib, Tag):
                if sib.name == "i":
                    entry_org = _clean_text(sib)
                    break
                if sib.name in ("br", "p"):
                    break
                i_child = sib.find("i") if hasattr(sib, "find") else None
                if i_child:
                    entry_org = _clean_text(i_child)
                    break
            sib = getattr(sib, "next_sibling", None)

        gene_entries.append(GeneEntry(
            name=entry_name,
            db=entry_db,
            description=entry_desc,
            organism=entry_org,
            gene_id=gene_id,
        ))

    # --- Paper counts: <a> with "curatedpaper::" logger ---
    for a in block.find_all("a", attrs={"onmousedown": re.compile(r"curatedpaper::")}):
        text = _clean_text(a)
        m = re.search(r"(\d+)\s*papers?", text)
        if m:
            total_curated_papers += int(m.group(1))
        elif "paper" in text.lower():
            total_curated_papers += 1

    # --- Identity / coverage: <a> with font-size:smaller style ---
    id_link = block.find(
        "a", style=re.compile(r"font-(?:family|size).*smaller|smaller.*font", re.I)
    )
    if id_link:
        id_text = _clean_text(id_link)
        id_m = re.search(r"(\d+)%\s*identity", id_text)
        cov_m = re.search(r"(\d+)%\s*coverage", id_text)
        if id_m:
            identity = f"{id_m.group(1)}%"
        if cov_m:
            coverage = f"{cov_m.group(1)}%"

    # --- Function / Subunit / Paper snippets / Ligand from trailing <UL>s ---
    # These are in <UL> siblings (lxml auto-closed the <p> before them).
    # Also check inside the block itself as fallback.
    all_lis: List[Tag] = []
    for ul in trailing_uls:
        all_lis.extend(ul.find_all("li", recursive=False))
    # Fallback: also check block children (in case html5lib or html.parser is used)
    all_lis.extend(block.find_all("li"))

    for li in all_lis:
        li_text = _clean_text(li)

        # function: tag
        func_b = li.find("b", string=re.compile(r"^function:", re.I))
        if func_b and not function_text:
            ft = re.sub(r"^function:\s*", "", li_text, flags=re.I)
            ft = re.split(r"\bsubunit:", ft, flags=re.I)[0].strip()
            if ft:
                function_text = ft
            continue

        # subunit: tag
        sub_b = li.find("b", string=re.compile(r"^subunit:", re.I))
        if sub_b and not subunit_text:
            subunit_text = re.sub(r"^subunit:\s*", "", li_text, flags=re.I).strip()
            continue

    # --- Paper snippets (text-mined): <a> with "pb::" logger ---
    search_targets = trailing_uls + [block]
    for target in search_targets:
        for a in target.find_all("a", attrs={"onmousedown": re.compile(r"pb::")}):
            s_title = _clean_text(a)
            s_url = a.get("href", "")
            if s_url.startswith("/"):
                s_url = BASE_URL + s_url
            s_citation = ""
            s_excerpt = ""

            small = a.find_next("small")
            if small:
                s_citation = _clean_text(small)

            parent_li = a.find_parent("li")
            if parent_li:
                inner_ul = parent_li.find("ul")
                if inner_ul:
                    for inner_li in inner_ul.find_all("li", recursive=False):
                        excerpt = _clean_text(inner_li)
                        if excerpt and ("\u201c" in excerpt or excerpt.startswith('"')):
                            s_excerpt = excerpt
                            break

            # Deduplicate
            if s_title and not any(s.title == s_title for s in paper_snippets):
                paper_snippets.append(PaperRef(
                    title=s_title,
                    url=s_url,
                    citation=s_citation,
                    snippet=s_excerpt,
                    source_db="text_mining",
                ))

    # Only return hits with real content
    if not gene_entries and not paper_snippets:
        return None

    # --- detail_id: extract from "More" link (litSearch.cgi?more=XXX) ---
    # The more= endpoint accepts bare accessions (P0AEZ3, Q01464, VIMSS115881)
    # but NOT locus tags (b1175) or curated:: gene_ids (MIND_ECOLI / P0AEZ3).
    search_targets = trailing_uls + [block]
    for target in search_targets:
        more_link = target.find("a", href=re.compile(r"litSearch\.cgi\?more="))
        if more_link:
            m = re.search(r"more=([^&\"\'>\s]+)", more_link.get("href", ""))
            if m:
                detail_id = m.group(1)
                break

    # Fallback: if no more= link, try to extract UniProt accession from
    # SwissProt gene entries.
    # Format 1: "UNIPROT_NAME / ACCESSION" (e.g. "MIND_ECOLI / P0AEZ3")
    # Format 2: bare accession (e.g. "A0KK56", "Q9HYZ6")
    if not detail_id:
        for ge in gene_entries:
            if not (ge.db and "SwissProt" in ge.db):
                continue
            if " / " in ge.name:
                parts = ge.name.split(" / ")
                if len(parts) == 2 and re.match(r"^[A-Z0-9]{4,10}$", parts[1].strip()):
                    detail_id = parts[1].strip()
                    break
            elif re.match(r"^[A-Z][A-Z0-9]{4,9}$", ge.name.strip()):
                # Bare UniProt accession (e.g. A0KK56, Q9HYZ6)
                detail_id = ge.name.strip()
                break

    # Determine paper_source: tells the agent whether gene_papers drill-down
    # will return results (curated) or come back empty (text_mining only)
    has_curated = total_curated_papers > 0
    has_text_mined = len(paper_snippets) > 0
    if has_curated and has_text_mined:
        paper_source = "both"
    elif has_curated:
        paper_source = "curated"
    elif has_text_mined:
        paper_source = "text_mining"
    else:
        paper_source = "unknown"

    return PaperBlastHit(
        gene_entries=gene_entries,
        identity=identity,
        coverage=coverage,
        function=function_text,
        subunit=subunit_text,
        total_curated_papers=total_curated_papers,
        paper_snippets=paper_snippets,
        paper_source=paper_source,
        detail_id=detail_id,
    )


def _parse_genome_search(
    soup: BeautifulSoup, max_genome_hits: int = 20
) -> CuratedBlastResults:
    """Parse genomeSearch.cgi (Curated BLAST) results into CuratedBlastResults.

    Curated BLAST has two modes:
      1. Without genome_id: returns a form page (no results).
      2. With genome_id: returns genome proteins + their characterized matches.

    The results page has one <table> per genome protein.  Row 0 is the
    genome protein (gene name, locus tag, accession, description).
    Rows 1+ (with alternating bgcolor #F2F2F2/#FCF3CF) are characterized
    protein matches from curated databases.

    We return one CuratedMatch per *genome protein*, with the best
    (first) characterized match embedded, capped at max_genome_hits.
    """
    query_info = ""
    matches: List[CuratedMatch] = []
    warnings: List[str] = []

    title_tag = soup.find("title")
    if title_tag:
        query_info = _clean_text(title_tag)

    # ------------------------------------------------------------------
    # Form-page detection: if the page has <select name="gdb"> and no
    # bgcolor rows, it's the query form, not a results page.
    # ------------------------------------------------------------------
    gdb_select = soup.find("select", attrs={"name": "gdb"})
    has_bgcolor = soup.find("tr", attrs={"bgcolor": True})
    if gdb_select and not has_bgcolor:
        warnings.append(
            "Curated BLAST returned the genome-selection form — no results. "
            "You must specify genome_id (e.g. 'GCF_000005845.2' for E. coli K-12) "
            "and genome_db (default 'NCBI'). Use gapmind_list_organisms or "
            "search NCBI Assembly to find a genome ID."
        )
        return CuratedBlastResults(
            query_info=query_info,
            total_matches=0,
            matches=[],
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Extract "Found N relevant proteins" count
    # ------------------------------------------------------------------
    total_genome_proteins = 0
    found_text = soup.find(string=re.compile(r"Found \d+ relevant protein"))
    if found_text:
        m = re.search(r"Found (\d+) relevant protein", found_text)
        if m:
            total_genome_proteins = int(m.group(1))

    # ------------------------------------------------------------------
    # Parse genome protein tables.
    # Each <table> block: row 0 = genome protein, rows 1+ = curated hits.
    # ------------------------------------------------------------------
    all_tables = soup.find_all("table")
    for table in all_tables:
        if len(matches) >= max_genome_hits:
            break

        rows = table.find_all("tr")
        if not rows:
            continue

        # Row 0: genome protein header (no bgcolor)
        header_row = rows[0]
        if header_row.get("bgcolor"):
            continue  # not a genome-protein table
        cells = header_row.find_all("td")
        if len(cells) < 2:
            continue
        genome_desc = _clean_text(cells[0])
        if not genome_desc or len(genome_desc) < 5:
            continue

        # Extract gene name, locus tag, accession from the header row links
        genome_links = []
        for a in header_row.find_all("a", href=True):
            href = a.get("href", "")
            text = _clean_text(a)
            if text and href and "litSearch" not in href:
                genome_links.append(ProteinLink(text=text, href=href))

        # Best curated match: first row with bgcolor
        best_desc = ""
        best_identity = ""
        best_links: List[ProteinLink] = []
        for row in rows[1:4]:  # check first 3 curated matches
            if not row.get("bgcolor"):
                continue
            curated_cells = row.find_all("td")
            if curated_cells:
                best_desc = _clean_text(curated_cells[0])[:300]
                if len(curated_cells) > 1:
                    best_identity = _clean_text(curated_cells[1])[:60]
                # Get curated protein link (first <a> in the row)
                for a in row.find_all("a", href=True):
                    href = a.get("href", "")
                    text = _clean_text(a)
                    if text and href and "showAlign" not in href:
                        best_links.append(ProteinLink(text=text, href=href))
                        break
                break  # only need the best match

        # Count total curated matches for this genome protein
        n_curated = sum(1 for r in rows[1:] if r.get("bgcolor"))

        matches.append(CuratedMatch(
            description=genome_desc[:300],
            details=(
                f"Best curated match ({best_identity}): {best_desc}"
                if best_desc else ""
            )[:400],
            organism="",
            identity=best_identity,
            coverage="",
            links=(genome_links[:3] + best_links[:1]),
        ))

    if total_genome_proteins and len(matches) < total_genome_proteins:
        warnings.append(
            f"Showing top {len(matches)} of {total_genome_proteins} genome "
            f"proteins. View all results at the search_url."
        )

    return CuratedBlastResults(
        query_info=query_info,
        total_matches=total_genome_proteins or len(matches),
        matches=matches,
        warnings=warnings,
    )


def _detect_gapmind_confidence(cell: Tag) -> str:
    """Detect GapMind confidence level from inline styles on <a> tags in a cell.

    Morgan's ScoreToStyle() uses:
      #007000 (green, bold) = high confidence (score > 1)
      #000000 (black)       = medium confidence (score = 1)
      #CC4444 (red)         = low confidence (score < 1)
    """
    for a in cell.find_all("a", style=True):
        style = a.get("style", "").lower()
        # High confidence: green (#007000) with bold
        if "#007000" in style or ("bold" in style and "00" in style):
            return "high"
        # Low confidence: red (#cc4444)
        if "#cc4444" in style or "#cc44" in style:
            return "low"
        # Medium confidence: black (#000000) — but only if style is explicitly set
        if "#000000" in style:
            return "medium"

    # Fallback: check row/cell bgcolor (older GapMind versions)
    style = cell.get("style", "").lower()
    parent_row = cell.find_parent("tr")
    if parent_row:
        style += parent_row.get("style", "").lower()
        bgcolor = (parent_row.get("bgcolor", "") or "").lower()
        if "green" in bgcolor or "#90" in bgcolor:
            return "high"
        if "yellow" in bgcolor or "#ff" in bgcolor:
            return "medium"
        if "red" in bgcolor or "#dd" in bgcolor:
            return "low"

    return "unknown"


def _parse_gapmind(soup: BeautifulSoup) -> GapMindResults:
    """Parse gapView.cgi (GapMind) organism results into GapMindResults."""
    organism = ""
    pathways: List[GapMindPathway] = []
    warnings: List[str] = []

    title_tag = soup.find("title")
    if title_tag:
        organism = _clean_text(title_tag)

    # GapMind encodes confidence via inline styles on <a> tags inside table cells.
    # From Morgan's ScoreToStyle() in gapView.cgi:
    #   score > 1 → color: #007000; font-weight: bold;   (high confidence)
    #   score = 1 → color: #000000;                      (medium confidence)
    #   score < 1 → color: #CC4444;                      (low confidence)
    # The style is on the <a> element, NOT on the <tr> or <td>.
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                # Detect confidence from <a> tag styles inside the first cell
                confidence = _detect_gapmind_confidence(cells[0])

                pw_name = _clean_text(cells[0])
                if pw_name and not pw_name.startswith("Pathway"):
                    raw_links = _extract_links(row)
                    pw_url = ""
                    for lk in raw_links:
                        if lk["href"] and "gapView" in lk["href"]:
                            pw_url = lk["href"]
                            break

                    pathways.append(GapMindPathway(
                        name=pw_name,
                        status=_clean_text(cells[1]) if len(cells) > 1 else "",
                        confidence=confidence,
                        url=pw_url,
                        links=[ProteinLink(text=lk["text"], href=lk["href"]) for lk in raw_links],
                    ))

    return GapMindResults(
        organism=organism,
        total_pathways=len(pathways),
        pathways=pathways,
        warnings=warnings,
    )


def _parse_organism_index(soup: BeautifulSoup) -> List[GapMindOrganism]:
    """Parse the GapMind organism index page into a list of GapMindOrganism.

    The organism index is at gapView.cgi?set=aa&orgs=orgsDef.
    Each organism is typically a link with orgId in the URL parameters.
    """
    organisms: List[GapMindOrganism] = []

    # GapMind organism index lists organisms as links with orgId parameter
    for a in soup.find_all("a", href=re.compile(r"orgId=")):
        href = a.get("href", "")
        org_id_match = re.search(r"orgId=([^&]+)", href)
        if org_id_match:
            org_id = org_id_match.group(1)
            name = _clean_text(a)
            if name and org_id:
                organisms.append(GapMindOrganism(
                    org_id=org_id,
                    name=name,
                ))

    return organisms


def _find_organism_id(
    organisms: List[GapMindOrganism], query: str
) -> Optional[GapMindOrganism]:
    """Fuzzy-match a user query against the GapMind organism index.

    Tries in order:
      1. Exact match (case-insensitive)
      2. Substring match
      3. difflib fuzzy match (cutoff=0.4)
    Returns the best-matching organism, or None.
    """
    query_lower = query.lower().strip()

    # 1. Exact match
    for org in organisms:
        if org.name.lower() == query_lower:
            return org

    # 2. Substring match (prefer shortest name that contains the query)
    substring_matches = [
        org for org in organisms if query_lower in org.name.lower()
    ]
    if substring_matches:
        # Return the shortest match (most specific)
        return min(substring_matches, key=lambda o: len(o.name))

    # 3. Fuzzy match via difflib
    name_map = {org.name.lower(): org for org in organisms}
    close = difflib.get_close_matches(query_lower, name_map.keys(), n=1, cutoff=0.4)
    if close:
        return name_map[close[0]]

    return None


# ---------------------------------------------------------------------------
# Pydantic input models
# ---------------------------------------------------------------------------

class PaperBlastInput(BaseModel):
    """Input for PaperBLAST protein literature search."""
    model_config = ConfigDict(str_strip_whitespace=True)

    query: str = Field(
        ...,
        description=(
            "Protein identifier or amino acid sequence. Accepts: "
            "UniProt accessions (e.g. 'P0AEZ3'), RefSeq protein IDs "
            "(e.g. 'WP_003246543.1'), VIMSS locus tags (e.g. 'VIMSS14484'), "
            "gene names with organism (e.g. 'acrB E. coli'), or raw amino "
            "acid sequences in single-letter code (no FASTA header needed)."
        ),
        min_length=2,
        max_length=50000,
    )

    max_hits: int = Field(
        default=25,
        description=(
            "Maximum number of hits to return. Default 25 keeps response size "
            "manageable for well-characterized proteins with hundreds of homologs. "
            "Set to -1 to return all hits (warning: can produce very large output). "
            "The total_found field always reflects the true count."
        ),
        ge=-1,
        le=1000,
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Query cannot be empty")
        # If it looks like a FASTA with header, strip the header
        if v.startswith(">"):
            lines = v.split("\n")
            v = "".join(line.strip() for line in lines[1:] if not line.startswith(">"))
        return v


class GeneIdInput(BaseModel):
    """Input for getting full paper list for a PaperBLAST gene."""
    model_config = ConfigDict(str_strip_whitespace=True)

    gene_id: str = Field(
        ...,
        description=(
            "Bare accession ID for the PaperBLAST 'more=' endpoint. "
            "Use the detail_id field from a prior paperblast_search hit "
            "(e.g. 'P0AEZ3', 'Q01464', 'VIMSS115881'). "
            "Do NOT use curated:: gene_ids like 'MIND_ECOLI / P0AEZ3' or "
            "locus tags like 'b1175' — these will fail."
        ),
        min_length=2,
    )


class CuratedBlastInput(BaseModel):
    """Input for Curated BLAST genome search."""
    model_config = ConfigDict(str_strip_whitespace=True)

    query: str = Field(
        ...,
        description=(
            "Functional description to search for, e.g. 'alcohol dehydrogenase', "
            "'transporter', 'two-component sensor kinase'. Searches curated "
            "databases (Swiss-Prot, BRENDA, MetaCyc, CharProtDB, etc.) for "
            "characterized proteins matching this description."
        ),
        min_length=2,
        max_length=500,
    )
    genome_db: str = Field(
        default="NCBI",
        description=(
            "Genome database to search against. Options: "
            "'NCBI' (RefSeq genomes), 'IMG' (JGI IMG), "
            "'UniProt' (UniProt proteomes), 'FitnessBrowser' "
            "(organisms with fitness data), 'MicrobesOnline'."
        ),
    )
    genome_id: Optional[str] = Field(
        default=None,
        description=(
            "Specific genome/assembly ID within the selected database. "
            "E.g. 'GCF_000005845.2' for E. coli K-12 in NCBI. "
            "If omitted, the tool will search across all genomes."
        ),
    )
    word_match: bool = Field(
        default=False,
        description="If true, restrict to whole-word matches only.",
    )
    max_genome_hits: int = Field(
        default=20,
        description=(
            "Maximum number of genome proteins to return (each with its "
            "best curated match). Default 20. The full results are always "
            "available at the search_url."
        ),
        ge=1,
        le=100,
    )


class GapMindSet(str, Enum):
    """GapMind analysis type."""
    AMINO_ACID = "aa"
    CARBON = "carbon"


class GapMindInput(BaseModel):
    """Input for GapMind metabolic gap analysis."""
    model_config = ConfigDict(str_strip_whitespace=True)

    analysis_type: GapMindSet = Field(
        default=GapMindSet.AMINO_ACID,
        description=(
            "Type of metabolic analysis: 'aa' for amino acid biosynthesis "
            "pathways, 'carbon' for carbon source utilization pathways."
        ),
    )
    organism: Optional[str] = Field(
        default=None,
        description=(
            "Organism name to search for (fuzzy-matched against GapMind index). "
            "E.g. 'Pseudomonas fluorescens', 'E. coli'. If omitted, returns "
            "the organism index so you can find the right org_id."
        ),
    )
    org_id: Optional[str] = Field(
        default=None,
        description=(
            "Direct GapMind organism identifier (e.g. 'FitnessBrowser__pseudo1_N1B4'). "
            "If provided, skips organism index lookup and goes straight to results. "
            "Get org_ids from gapmind_list_organisms or a prior gapmind_check call."
        ),
    )


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

@mcp.tool(
    name="paperblast_search",
    annotations={
        "title": "PaperBLAST: Find Papers About a Protein",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def paperblast_search(params: PaperBlastInput) -> str:
    """Search PaperBLAST for scientific literature about a protein or its homologs.

    Given a protein sequence or identifier, runs BLAST against the PaperBLAST
    database (~800K proteins linked to ~1.3M papers) and returns structured
    results including homologous proteins with their associated publications.

    Data sources include: EuropePMC text mining, Swiss-Prot, BRENDA, MetaCyc,
    EcoCyc, TCDB, REBASE, CharProtDB, CAZy, BioLiP, GeneRIF, and the
    Fitness Browser.

    Args:
        params: PaperBlastInput with query (protein sequence or identifier)

    Returns:
        JSON with hits (homologous proteins) each containing papers with PMIDs.
        Also includes the URL for the full HTML results page.
    """
    try:
        soup = await _get("litSearch.cgi", {"query": params.query})
        results = _parse_litsearch_results(soup)
        results.search_url = f"{CGI}/litSearch.cgi?query={params.query}"

        # Truncate to max_hits (default 25) to keep output manageable
        if params.max_hits >= 0 and len(results.hits) > params.max_hits:
            results.warnings.append(
                f"Returning top {params.max_hits} of {results.total_found} hits. "
                f"Use max_hits to retrieve more (up to 1000) or -1 for all."
            )
            results.hits = results.hits[:params.max_hits]

        return results.model_dump_json(indent=2)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="paperblast_gene_papers",
    annotations={
        "title": "PaperBLAST: Full Paper List for a Gene",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def paperblast_gene_papers(params: GeneIdInput) -> str:
    """Get the complete list of papers for a specific gene in PaperBLAST.

    Use this after paperblast_search to drill into a specific hit and
    retrieve all associated publications. Pass the detail_id from
    the search hit (a bare accession like 'P0AEZ3'), NOT the
    curated:: gene_id or a locus tag.

    Args:
        params: GeneIdInput with gene_id (bare accession from detail_id)

    Returns:
        JSON with the full paper list for that gene.
    """
    try:
        # Clean up common wrong formats:
        # "MIND_ECOLI / P0AEZ3" → "P0AEZ3"
        # "SwissProt::P0AEZ3" → "P0AEZ3"
        gene_id = params.gene_id.strip()
        if " / " in gene_id:
            gene_id = gene_id.split(" / ")[-1].strip()
        if "::" in gene_id:
            gene_id = gene_id.split("::")[-1].strip()

        soup = await _get("litSearch.cgi", {"more": gene_id})
        pb_results = _parse_litsearch_results(soup)
        detail_url = f"{CGI}/litSearch.cgi?more={gene_id}"

        warnings = list(pb_results.warnings)

        # The more= page doesn't have "Found X similar proteins" text,
        # so total_found stays 0. Compute from actual hit content instead.
        total_found = pb_results.total_found
        if total_found == 0 and pb_results.hits:
            # Sum curated papers + text-mined snippets across hits
            total_found = sum(
                h.total_curated_papers + len(h.paper_snippets)
                for h in pb_results.hits
            )

        if total_found == 0 and not pb_results.hits:
            warnings.append(
                f"No papers found for '{gene_id}'. "
                f"Possible causes: (1) the gene_id format is wrong — use "
                f"the detail_id from paperblast_search, not gene_entries[].gene_id; "
                f"(2) this gene's literature associations are from EuropePMC "
                f"text mining only (paper_source='text_mining' in the search "
                f"results). View the detail page: {detail_url}"
            )

        results = GenePapersResults(
            gene_id=gene_id,
            total_found=total_found,
            hits=pb_results.hits,
            detail_url=detail_url,
            warnings=warnings,
        )
        return results.model_dump_json(indent=2)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="curated_blast_search",
    annotations={
        "title": "Curated BLAST: Find Characterized Proteins by Function",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def curated_blast_search(params: CuratedBlastInput) -> str:
    """Search for characterized proteins matching a functional description.

    Curated BLAST (genomeSearch.cgi) searches curated databases of
    experimentally-characterized proteins (Swiss-Prot, BRENDA, MetaCyc,
    CharProtDB, etc.) for entries matching your description, then BLASTs
    them against a genome to find homologs.

    Args:
        params: CuratedBlastInput with functional query and optional genome

    Returns:
        JSON with matching characterized proteins and their genome homologs.
    """
    try:
        cgi_params: Dict[str, str] = {"query": params.query}
        if params.genome_db:
            cgi_params["gdb"] = params.genome_db
        if params.genome_id:
            cgi_params["gid"] = params.genome_id
        if params.word_match:
            cgi_params["word"] = "1"

        soup = await _get("genomeSearch.cgi", cgi_params)
        results = _parse_genome_search(soup, max_genome_hits=params.max_genome_hits)
        results.search_url = f"{CGI}/genomeSearch.cgi?query={params.query}"
        return results.model_dump_json(indent=2)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="gapmind_check",
    annotations={
        "title": "GapMind: Metabolic Pathway Gap Analysis",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def gapmind_check(params: GapMindInput) -> str:
    """Check metabolic pathway completeness for an organism using GapMind.

    GapMind predicts which amino acids an organism can synthesize (set=aa)
    or which carbon sources it can catabolize (set=carbon) by analyzing
    annotated pathways. Returns confidence levels: high (green),
    medium (yellow), or low/gap (red) for each pathway.

    Three modes:
      1. org_id provided → direct lookup (fastest)
      2. organism name provided → fetch index, fuzzy match, then results
      3. Neither → return organism index for browsing

    Args:
        params: GapMindInput with analysis_type and optional organism/org_id

    Returns:
        JSON: GapMindResults (with pathways) or GapMindOrganismIndex (organism list).
    """
    set_val = params.analysis_type.value
    try:
        # --- Mode 1: Direct org_id lookup ---
        if params.org_id:
            cgi_params = {
                "set": set_val,
                "orgs": "orgsDef",
                "orgId": params.org_id,
            }
            soup = await _get("gapView.cgi", cgi_params)
            results = _parse_gapmind(soup)
            results.org_id = params.org_id
            results.analysis_type = set_val
            results.gapmind_url = (
                f"{CGI}/gapView.cgi?set={set_val}&orgs=orgsDef&orgId={params.org_id}"
            )
            return results.model_dump_json(indent=2)

        # --- Mode 2: Organism name → fuzzy match via index ---
        if params.organism:
            # Step 1: Fetch organism index
            index_soup = await _get("gapView.cgi", {"set": set_val, "orgs": "orgsDef"})
            organisms = _parse_organism_index(index_soup)

            if not organisms:
                return GapMindOrganismIndex(
                    analysis_type=set_val,
                    total_organisms=0,
                    organisms=[],
                    index_url=f"{CGI}/gapView.cgi?set={set_val}&orgs=orgsDef",
                    warnings=["No organisms found in index. The organism index page "
                              "may have changed format."],
                ).model_dump_json(indent=2)

            # Step 2: Fuzzy match
            match = _find_organism_id(organisms, params.organism)
            if not match:
                # Return index with top suggestions
                return GapMindOrganismIndex(
                    analysis_type=set_val,
                    total_organisms=len(organisms),
                    organisms=organisms[:20],  # first 20 as suggestions
                    index_url=f"{CGI}/gapView.cgi?set={set_val}&orgs=orgsDef",
                    warnings=[
                        f"No organism matching '{params.organism}' found in GapMind. "
                        f"Showing first 20 of {len(organisms)} available organisms. "
                        f"Try a more specific name or use an org_id directly."
                    ],
                ).model_dump_json(indent=2)

            # Step 3: Fetch results for matched organism
            cgi_params = {
                "set": set_val,
                "orgs": "orgsDef",
                "orgId": match.org_id,
            }
            soup = await _get("gapView.cgi", cgi_params)
            results = _parse_gapmind(soup)
            results.org_id = match.org_id
            results.analysis_type = set_val
            results.gapmind_url = (
                f"{CGI}/gapView.cgi?set={set_val}&orgs=orgsDef&orgId={match.org_id}"
            )
            if match.name.lower() != params.organism.lower():
                results.warnings.append(
                    f"Fuzzy matched '{params.organism}' → '{match.name}' (orgId: {match.org_id})"
                )
            return results.model_dump_json(indent=2)

        # --- Mode 3: No organism → return index ---
        index_soup = await _get("gapView.cgi", {"set": set_val, "orgs": "orgsDef"})
        organisms = _parse_organism_index(index_soup)
        return GapMindOrganismIndex(
            analysis_type=set_val,
            total_organisms=len(organisms),
            organisms=organisms,
            index_url=f"{CGI}/gapView.cgi?set={set_val}&orgs=orgsDef",
        ).model_dump_json(indent=2)

    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="gapmind_list_organisms",
    annotations={
        "title": "GapMind: List Available Organisms",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def gapmind_list_organisms(params: GapMindInput) -> str:
    """List organisms available in GapMind's pre-computed analysis.

    GapMind only has results for organisms that have been pre-computed.
    Use this tool to find available organisms and their org_ids before
    calling gapmind_check.

    Args:
        params: GapMindInput with analysis_type (organism/org_id fields ignored)

    Returns:
        JSON with GapMindOrganismIndex listing all available organisms.
    """
    set_val = params.analysis_type.value
    try:
        soup = await _get("gapView.cgi", {"set": set_val, "orgs": "orgsDef"})
        organisms = _parse_organism_index(soup)
        return GapMindOrganismIndex(
            analysis_type=set_val,
            total_organisms=len(organisms),
            organisms=organisms,
            index_url=f"{CGI}/gapView.cgi?set={set_val}&orgs=orgsDef",
        ).model_dump_json(indent=2)
    except Exception as e:
        return _handle_error(e)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if "--http" in sys.argv:
        mcp.run(transport="streamable_http", port=8765)
    else:
        mcp.run()
