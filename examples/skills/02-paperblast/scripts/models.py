"""
Pydantic output models for PaperBLAST MCP tools.

These models define the structured return types for all five tools:
  - PaperBlastResults      → paperblast_search
  - GenePapersResults      → paperblast_gene_papers
  - CuratedBlastResults    → curated_blast_search
  - GapMindResults         → gapmind_check
  - GapMindOrganismIndex   → gapmind_check (no organism) / gapmind_list_organisms

Each model is self-documenting via Field(description=...) so that JSON Schema
introspection reveals what every field means — useful for downstream agents.

Separate from paperblast_mcp.py for:
  - Teaching clarity: input models vs output models vs server logic
  - Independent import by test scripts
  - Keeping the main server file under 800 lines
"""

from __future__ import annotations

from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Shared building blocks
# ---------------------------------------------------------------------------

class PaperRef(BaseModel):
    """A reference to a scientific paper linked to a protein."""
    model_config = ConfigDict(str_strip_whitespace=True)

    pmid: Optional[str] = Field(
        default=None,
        description="PubMed identifier, if available (e.g. '12345678').",
    )
    title: str = Field(
        default="",
        description="Paper title or link text as shown in PaperBLAST.",
    )
    snippet: str = Field(
        default="",
        description=(
            "Relevant text excerpt from the paper mentioning the protein. "
            "May contain HTML markup from text-mining highlights."
        ),
    )
    citation: str = Field(
        default="",
        description="Author, journal, and year string (e.g. 'Smith et al., Nature 2020').",
    )
    url: str = Field(
        default="",
        description="Direct URL to the paper (PubMed, DOI, or EuropePMC).",
    )
    source_db: str = Field(
        default="",
        description=(
            "Database source: 'text_mining' for EuropePMC hits, "
            "or the curated database name (Swiss-Prot, BRENDA, etc.)."
        ),
    )


class ProteinLink(BaseModel):
    """A hyperlink extracted from result HTML, typically to a database entry."""
    model_config = ConfigDict(str_strip_whitespace=True)

    text: str = Field(default="", description="Display text of the link.")
    href: str = Field(default="", description="Full URL target.")
    database: str = Field(
        default="",
        description="Inferred database (e.g. 'UniProt', 'PDB', 'KEGG').",
    )


# ---------------------------------------------------------------------------
# PaperBLAST search results (litSearch.cgi)
# ---------------------------------------------------------------------------

class GeneEntry(BaseModel):
    """A curated database entry for a gene within a PaperBLAST hit."""
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        default="",
        description="Gene or protein name as shown in PaperBLAST.",
    )
    db: str = Field(
        default="",
        description="Source database (e.g. 'SwissProt', 'CharProtDB', 'BRENDA').",
    )
    description: str = Field(
        default="",
        description="Functional description from the curated database.",
    )
    organism: str = Field(
        default="",
        description="Source organism (e.g. 'Escherichia coli K-12').",
    )
    gene_id: str = Field(
        default="",
        description=(
            "PaperBLAST gene identifier for drill-down via paperblast_gene_papers "
            "(e.g. 'VIMSS14484', 'SwissProt::P0AEZ3')."
        ),
    )


class PaperBlastHit(BaseModel):
    """A single BLAST hit from PaperBLAST with associated literature."""
    model_config = ConfigDict(str_strip_whitespace=True)

    gene_entries: List[GeneEntry] = Field(
        default_factory=list,
        description="Curated database entries for this hit protein.",
    )
    identity: str = Field(
        default="",
        description="Sequence identity to query (e.g. '100%', '45%').",
    )
    coverage: str = Field(
        default="",
        description="Query coverage (e.g. '100%', '89%').",
    )
    function: str = Field(
        default="",
        description=(
            "Experimentally characterized function from curated databases. "
            "Empty for text-mining-only hits."
        ),
    )
    subunit: str = Field(
        default="",
        description="Subunit composition or complex membership, if annotated.",
    )
    total_curated_papers: int = Field(
        default=0,
        description="Number of curated papers linked to this gene.",
    )
    paper_snippets: List[PaperRef] = Field(
        default_factory=list,
        description="Text-mined paper references with relevant excerpts.",
    )
    paper_source: str = Field(
        default="unknown",
        description=(
            "How literature is linked to this protein: "
            "'curated' (papers from Swiss-Prot, BRENDA, etc. — drillable via gene_papers), "
            "'text_mining' (EuropePMC text mining only — gene_papers will return empty), "
            "'both' (curated + text-mined papers)."
        ),
    )
    detail_id: str = Field(
        default="",
        description=(
            "ID to pass to paperblast_gene_papers for this hit's full paper list. "
            "Extracted from the 'More' link in search results (bare accession like "
            "'P0AEZ3' or 'Q01464'). Empty if the hit has too few papers for a "
            "detail page. Use this value — not gene_entries[].gene_id — as the "
            "gene_id argument to paperblast_gene_papers."
        ),
    )


class PaperBlastResults(BaseModel):
    """Complete results from a PaperBLAST protein literature search."""
    model_config = ConfigDict(str_strip_whitespace=True)

    query_info: str = Field(
        default="",
        description=(
            "Parsed header showing query protein identity "
            "(e.g. 'P0AEZ3 MinD (Escherichia coli) (270 a.a.)')."
        ),
    )
    total_found: int = Field(
        default=0,
        description="Total number of similar proteins found in literature.",
    )
    hits: List[PaperBlastHit] = Field(
        default_factory=list,
        description="BLAST hits ordered by sequence similarity (best first).",
    )
    search_url: str = Field(
        default="",
        description="URL to view full results in a browser.",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Parser warnings (e.g. unexpected HTML structure).",
    )


# ---------------------------------------------------------------------------
# Gene papers drill-down (litSearch.cgi?more=GENE_ID)
# ---------------------------------------------------------------------------

class GenePapersResults(BaseModel):
    """Full paper list for a specific PaperBLAST gene."""
    model_config = ConfigDict(str_strip_whitespace=True)

    gene_id: str = Field(
        default="",
        description="The gene identifier that was queried.",
    )
    total_found: int = Field(
        default=0,
        description="Total papers found for this gene.",
    )
    hits: List[PaperBlastHit] = Field(
        default_factory=list,
        description="Paper hits for this gene.",
    )
    detail_url: str = Field(
        default="",
        description="URL to view full paper list in a browser.",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Parser warnings.",
    )


# ---------------------------------------------------------------------------
# Curated BLAST results (genomeSearch.cgi)
# ---------------------------------------------------------------------------

class CuratedMatch(BaseModel):
    """A characterized protein match from Curated BLAST."""
    model_config = ConfigDict(str_strip_whitespace=True)

    description: str = Field(
        default="",
        description="Functional description of the characterized protein.",
    )
    details: str = Field(
        default="",
        description="Additional details (organism, accession, evidence).",
    )
    organism: str = Field(
        default="",
        description="Source organism of the characterized protein.",
    )
    identity: str = Field(
        default="",
        description="Sequence identity to genome homolog (if available).",
    )
    coverage: str = Field(
        default="",
        description="Query coverage (if available).",
    )
    links: List[ProteinLink] = Field(
        default_factory=list,
        description="Links to database entries and alignments.",
    )


class CuratedBlastResults(BaseModel):
    """Results from a Curated BLAST functional search."""
    model_config = ConfigDict(str_strip_whitespace=True)

    query_info: str = Field(
        default="",
        description="Search query description from page title.",
    )
    total_matches: int = Field(
        default=0,
        description="Number of characterized proteins found.",
    )
    matches: List[CuratedMatch] = Field(
        default_factory=list,
        description="Characterized protein matches.",
    )
    search_url: str = Field(
        default="",
        description="URL to view full results in a browser.",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Parser warnings.",
    )


# ---------------------------------------------------------------------------
# GapMind metabolic gap analysis (gapView.cgi)
# ---------------------------------------------------------------------------

class GapMindOrganism(BaseModel):
    """An organism available in the GapMind pre-computed index."""
    model_config = ConfigDict(str_strip_whitespace=True)

    org_id: str = Field(
        description=(
            "GapMind organism identifier for querying results "
            "(e.g. 'FitnessBrowser__pseudo1_N1B4'). "
            "Pass this as org_id to gapmind_check for direct lookup."
        ),
    )
    name: str = Field(
        default="",
        description="Display name of the organism (e.g. 'Pseudomonas fluorescens FW300-N1B4').",
    )
    taxonomy: str = Field(
        default="",
        description="Taxonomic lineage or NCBI taxonomy ID, if available.",
    )


class GapMindStep(BaseModel):
    """A single enzymatic step within a GapMind pathway."""
    model_config = ConfigDict(str_strip_whitespace=True)

    gene: str = Field(
        default="",
        description="Gene or enzyme name for this step (e.g. 'hisA', 'prs').",
    )
    status: str = Field(
        default="",
        description="Step status: 'found', 'gap', or 'low_confidence'.",
    )
    best_hit_id: Optional[str] = Field(
        default=None,
        description="Protein ID of the best BLAST hit for this step.",
    )
    identity: Optional[float] = Field(
        default=None,
        description="Percent sequence identity to characterized protein.",
    )
    description: str = Field(
        default="",
        description="Brief functional description of this step.",
    )


class GapMindPathway(BaseModel):
    """A metabolic pathway assessed by GapMind."""
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        default="",
        description="Pathway name (e.g. 'histidine biosynthesis', 'L-proline biosynthesis').",
    )
    status: str = Field(
        default="",
        description="Summary status text from GapMind.",
    )
    confidence: str = Field(
        default="unknown",
        description=(
            "Overall confidence: 'high' (all steps found), "
            "'medium' (some steps low-confidence), "
            "'low' (missing steps / gaps)."
        ),
    )
    score: Optional[float] = Field(
        default=None,
        description="Numeric completeness score (0.0-1.0), if available.",
    )
    url: str = Field(
        default="",
        description="Direct link to the detailed pathway view in GapMind.",
    )
    steps: Optional[List[GapMindStep]] = Field(
        default=None,
        description=(
            "Individual enzymatic steps (only populated for detailed views, "
            "not the summary table)."
        ),
    )
    links: List[ProteinLink] = Field(
        default_factory=list,
        description="Links extracted from the pathway row.",
    )


class GapMindResults(BaseModel):
    """Organism-specific GapMind metabolic gap analysis results."""
    model_config = ConfigDict(str_strip_whitespace=True)

    organism: str = Field(
        default="",
        description="Organism name from the results page.",
    )
    org_id: str = Field(
        default="",
        description="The GapMind organism ID that was queried.",
    )
    analysis_type: str = Field(
        default="",
        description="Analysis type: 'aa' (amino acid biosynthesis) or 'carbon' (carbon sources).",
    )
    total_pathways: int = Field(
        default=0,
        description="Total number of pathways assessed.",
    )
    pathways: List[GapMindPathway] = Field(
        default_factory=list,
        description="Pathway assessments ordered as in GapMind output.",
    )
    gapmind_url: str = Field(
        default="",
        description="URL to view full results in a browser.",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Parser warnings.",
    )


class GapMindOrganismIndex(BaseModel):
    """Index of organisms available in GapMind for a given analysis type."""
    model_config = ConfigDict(str_strip_whitespace=True)

    analysis_type: str = Field(
        default="",
        description="Analysis type: 'aa' or 'carbon'.",
    )
    total_organisms: int = Field(
        default=0,
        description="Number of organisms in the index.",
    )
    organisms: List[GapMindOrganism] = Field(
        default_factory=list,
        description=(
            "Available organisms. Use org_id values to query gapmind_check "
            "for organism-specific results."
        ),
    )
    index_url: str = Field(
        default="",
        description="URL to view the organism index in a browser.",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Parser warnings.",
    )
