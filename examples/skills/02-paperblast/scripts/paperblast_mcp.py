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

def _parse_litsearch_results(soup: BeautifulSoup) -> Dict[str, Any]:
    """Parse litSearch.cgi HTML into structured hit list."""
    results: Dict[str, Any] = {
        "hits": [],
        "query_info": "",
        "total_found": 0,
        "warnings": [],
    }

    # --- Header ---
    h3 = soup.find("h3")
    if h3:
        results["query_info"] = _clean_text(h3)

    # --- Total count ---
    for p in soup.find_all("p"):
        m = re.search(r"Found\s+(\d+)\s+similar\s+proteins?", _clean_text(p))
        if m:
            results["total_found"] = int(m.group(1))
            break

    # --- Warnings / errors ---
    for p in soup.find_all("p"):
        text = _clean_text(p)
        if re.search(r"\b(sorry|error|no results|no hits|not found)\b", text, re.I):
            results["warnings"].append(text)

    # --- Hit blocks: <p style="margin-top: 1em ..."> ---
    # IMPORTANT: lxml auto-closes <p> when it encounters block-level <UL>.
    # In Morgan's HTML the <UL> with function/subunit/snippets is written
    # inside the <p>, but lxml parses it as a SIBLING.  So we must collect
    # trailing <UL> siblings that belong to each hit <p>.
    hit_blocks = soup.find_all("p", style=re.compile(r"margin-top:\s*1em"))

    for block in hit_blocks:
        # Walk forward through siblings, collecting <ul>s until next <p>
        trailing_uls: List[Tag] = []
        sib = block.next_sibling
        while sib is not None:
            if isinstance(sib, Tag):
                if sib.name == "p":
                    break  # next hit or other paragraph
                if sib.name == "ul":
                    trailing_uls.append(sib)
            sib = sib.next_sibling

        hit = _parse_hit_block(block, trailing_uls)
        if hit:
            results["hits"].append(hit)

    results["total_hits"] = len(results["hits"])
    results["total_paper_snippets"] = sum(
        len(h.get("paper_snippets", [])) for h in results["hits"]
    )
    return results


def _parse_hit_block(block: Tag, trailing_uls: List[Tag] = None) -> Optional[Dict[str, Any]]:
    """Parse a single PaperBLAST hit <p> block + trailing <UL> siblings."""
    if trailing_uls is None:
        trailing_uls = []
    hit: Dict[str, Any] = {
        "gene_entries": [],
        "identity": "",
        "coverage": "",
        "alignment_detail": "",
        "function": "",
        "subunit": "",
        "paper_snippets": [],
        "total_curated_papers": 0,
    }

    # --- Gene entries: <a> with onmousedown containing "curated::" ---
    for a in block.find_all("a", attrs={"onmousedown": re.compile(r"curated::")}):
        md = re.search(r"curated::(.+?)(?:'|\")", a.get("onmousedown", ""))
        gene_id = md.group(1).strip() if md else _clean_text(a)

        entry: Dict[str, str] = {
            "id": gene_id,
            "name": _clean_text(a),
            "db": a.get("title", ""),
            "url": a.get("href", ""),
            "description": "",
            "organism": "",
        }

        # Description: <b> tag that is a next sibling of this <a>
        # Walk forward through siblings to find the first <b>
        sib = a.next_sibling
        while sib is not None:
            if isinstance(sib, Tag):
                if sib.name == "b":
                    entry["description"] = _clean_text(sib)
                    break
                if sib.name in ("br", "a", "ul", "p"):
                    break  # passed into next entry or section
            sib = getattr(sib, "next_sibling", None)

        # Organism: first <i> after this <a>, before next <BR> or <a>
        sib = a.next_sibling
        while sib is not None:
            if isinstance(sib, Tag):
                if sib.name == "i":
                    entry["organism"] = _clean_text(sib)
                    break
                if sib.name in ("br", "p"):
                    break
                # Check children of intervening text nodes
                i_child = sib.find("i") if hasattr(sib, "find") else None
                if i_child:
                    entry["organism"] = _clean_text(i_child)
                    break
            sib = getattr(sib, "next_sibling", None)

        hit["gene_entries"].append(entry)

    # --- Paper counts: <a> with "curatedpaper::" logger ---
    total_papers = 0
    for a in block.find_all("a", attrs={"onmousedown": re.compile(r"curatedpaper::")}):
        text = _clean_text(a)
        m = re.search(r"(\d+)\s*papers?", text)
        if m:
            total_papers += int(m.group(1))
        elif "paper" in text.lower():
            total_papers += 1  # "paper" (singular, no number) = 1
    hit["total_curated_papers"] = total_papers

    # --- Identity / coverage: <a> with font-size:smaller style ---
    id_link = block.find(
        "a", style=re.compile(r"font-(?:family|size).*smaller|smaller.*font", re.I)
    )
    if id_link:
        id_text = _clean_text(id_link)
        id_m = re.search(r"(\d+)%\s*identity", id_text)
        cov_m = re.search(r"(\d+)%\s*coverage", id_text)
        if id_m:
            hit["identity"] = f"{id_m.group(1)}%"
        if cov_m:
            hit["coverage"] = f"{cov_m.group(1)}%"
        hit["alignment_detail"] = id_link.get("title", "")

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
        if func_b and not hit["function"]:
            func_text = re.sub(r"^function:\s*", "", li_text, flags=re.I)
            func_text = re.split(r"\bsubunit:", func_text, flags=re.I)[0].strip()
            if func_text:
                hit["function"] = func_text
            continue

        # subunit: tag
        sub_b = li.find("b", string=re.compile(r"^subunit:", re.I))
        if sub_b and not hit["subunit"]:
            hit["subunit"] = re.sub(r"^subunit:\s*", "", li_text, flags=re.I).strip()
            continue

        # Ligand info (BioLiP/PDB entries)
        if li_text.lower().startswith("ligand:") and "ligand" not in hit:
            hit["ligand"] = li_text
            continue

    # --- Paper snippets (text-mined): <a> with "pb::" logger ---
    # Search in trailing ULs and block
    search_targets = trailing_uls + [block]
    for target in search_targets:
        for a in target.find_all("a", attrs={"onmousedown": re.compile(r"pb::")}):
            snippet: Dict[str, str] = {
                "title": _clean_text(a),
                "url": a.get("href", ""),
                "citation": "",
                "excerpt": "",
            }
            if snippet["url"].startswith("/"):
                snippet["url"] = BASE_URL + snippet["url"]

            # Citation: <small> tag after the paper link
            small = a.find_next("small")
            if small:
                snippet["citation"] = _clean_text(small)

            # Excerpt: text in nested <UL><LI> with curly quotes
            parent_li = a.find_parent("li")
            if parent_li:
                inner_ul = parent_li.find("ul")
                if inner_ul:
                    for inner_li in inner_ul.find_all("li", recursive=False):
                        excerpt = _clean_text(inner_li)
                        if excerpt and ("\u201c" in excerpt or excerpt.startswith('"')):
                            snippet["excerpt"] = excerpt
                            break

            # Deduplicate
            if snippet["title"] and not any(
                s["title"] == snippet["title"] for s in hit["paper_snippets"]
            ):
                hit["paper_snippets"].append(snippet)

    # --- Build primary summary from first gene entry ---
    if hit["gene_entries"]:
        primary = hit["gene_entries"][0]
        hit["primary_name"] = primary["name"]
        hit["primary_description"] = primary["description"]
        hit["primary_organism"] = primary["organism"]
        hit["primary_db"] = primary["db"]

    # Only return hits with real content
    if hit["gene_entries"] or hit["paper_snippets"]:
        return hit
    return None


def _parse_genome_search(soup: BeautifulSoup) -> Dict[str, Any]:
    """Parse genomeSearch.cgi (Curated BLAST) results."""
    results = {"matches": [], "query_info": "", "warnings": []}

    title_tag = soup.find("title")
    if title_tag:
        results["query_info"] = _clean_text(title_tag)

    # Curated BLAST results show characterized proteins with descriptions
    # and similarity metrics, rendered as HTML tables or structured divs
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        for row in rows[1:]:  # skip header
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                match = {
                    "description": _clean_text(cells[0]),
                    "details": _clean_text(cells[1]) if len(cells) > 1 else "",
                    "links": _extract_links(row)
                }
                if match["description"]:
                    results["matches"].append(match)

    results["total_matches"] = len(results["matches"])
    return results


def _parse_gapmind(soup: BeautifulSoup) -> Dict[str, Any]:
    """Parse gapView.cgi (GapMind) results."""
    results = {"pathways": [], "organism": "", "warnings": []}

    title_tag = soup.find("title")
    if title_tag:
        results["organism"] = _clean_text(title_tag)

    # GapMind uses color-coded tables: green=high-confidence, yellow=medium, red=gap
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                # Check for background color indicating confidence
                style = row.get("style", "") + cells[0].get("style", "")
                bgcolor = row.get("bgcolor", "") or cells[0].get("bgcolor", "")

                confidence = "unknown"
                if "green" in style.lower() or "green" in bgcolor.lower() or "#90" in bgcolor:
                    confidence = "high"
                elif "yellow" in style.lower() or "yellow" in bgcolor.lower() or "#FF" in bgcolor:
                    confidence = "medium"
                elif "red" in style.lower() or "red" in bgcolor.lower() or "#DD" in bgcolor:
                    confidence = "low"

                pathway = {
                    "name": _clean_text(cells[0]),
                    "status": _clean_text(cells[1]) if len(cells) > 1 else "",
                    "confidence": confidence,
                    "links": _extract_links(row)
                }
                if pathway["name"] and not pathway["name"].startswith("Pathway"):
                    results["pathways"].append(pathway)

    results["total_pathways"] = len(results["pathways"])
    return results


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
            "PaperBLAST gene identifier. Typically a locus tag or accession "
            "returned from a prior paperblast_search result (e.g. 'VIMSS14484', "
            "'SwissProt::P0AEZ3')."
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
            "Organism name or identifier to analyze. If omitted, returns "
            "the GapMind overview/search page content."
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
        results["search_url"] = f"{CGI}/litSearch.cgi?query={params.query}"
        return json.dumps(results, indent=2, ensure_ascii=False)
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
    retrieve all associated publications (up to 10,000).

    Args:
        params: GeneIdInput with gene_id from a prior search result

    Returns:
        JSON with the full paper list for that gene.
    """
    try:
        soup = await _get("litSearch.cgi", {"more": params.gene_id})
        results = _parse_litsearch_results(soup)
        results["gene_id"] = params.gene_id
        results["detail_url"] = f"{CGI}/litSearch.cgi?more={params.gene_id}"
        return json.dumps(results, indent=2, ensure_ascii=False)
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
        results = _parse_genome_search(soup)
        results["search_url"] = f"{CGI}/genomeSearch.cgi?query={params.query}"
        return json.dumps(results, indent=2, ensure_ascii=False)
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

    Args:
        params: GapMindInput with analysis_type and optional organism

    Returns:
        JSON with pathway predictions and confidence levels.
    """
    try:
        cgi_params: Dict[str, str] = {"set": params.analysis_type.value}
        if params.organism:
            cgi_params["orgs"] = params.organism

        soup = await _get("gapView.cgi", cgi_params)
        results = _parse_gapmind(soup)
        results["analysis_type"] = params.analysis_type.value
        results["gapmind_url"] = f"{CGI}/gapView.cgi?set={params.analysis_type.value}"
        return json.dumps(results, indent=2, ensure_ascii=False)
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
