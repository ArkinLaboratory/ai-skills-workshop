# Public Skills and MCP Servers for Computational Biology

A curated guide to Claude skills and Model Context Protocol (MCP) servers relevant to computational biology, microbiology, and genomics research.

---

## Section 1: Where to Find Skills and MCPs

| Directory | URL | What's There |
|-----------|-----|-------------|
| Anthropic Life Sciences | github.com/anthropics/life-sciences | Official Anthropic marketplace for bio/life science skills and MCPs |
| Anthropic Skills Repo | github.com/anthropics/skills | Official production-ready Claude Code skills |
| Official MCP Servers | github.com/modelcontextprotocol/servers | Reference MCP server implementations from the MCP project |
| PulseMCP | pulsemcp.com | 8,000+ community MCP servers, searchable |
| mcp.so | mcp.so | 17,000+ MCP servers with search |
| Glama (Bioinformatics) | glama.ai/mcp/servers/categories/bioinformatics | Bioinformatics-filtered MCP directory |
| MCPmed | github.com/MCPmed | Bioinformatics-focused MCP servers |
| Augmented-Nature | github.com/Augmented-Nature | Comprehensive biology MCP servers |
| SkillsMP | skillsmp.com | Agent skills marketplace |
| Awesome Claude Skills | github.com/travisvn/awesome-claude-skills | Curated skills list |

**Tip:** Searching GitHub for "biology MCP", "genomics MCP", "bioinformatics MCP", or "microbiology MCP" often uncovers relevant projects not yet listed in marketplaces.

---

## Section 2: Recommended for Our Group

Curated list organized by category. Each entry includes the name, repository URL, description, and relevance to our research.

### Sequence & Protein Databases

**1. UniProt MCP Server**
- **Repo:** github.com/Augmented-Nature/Augmented-Nature-UniProt-MCP-Server
- **What it does:** 26+ tools for protein sequence search, feature analysis, cross-references, homolog identification, and functional annotation.
- **Relevant for:** Protein characterization, functional annotation, evolutionary analysis, and sequence comparison workflows.

**2. Ensembl MCP Server**
- **Repo:** github.com/Augmented-Nature/Ensembl-MCP-Server
- **What it does:** 30+ tools for gene lookup, sequence retrieval, genetic variant data, cross-species homology, and regulatory element queries.
- **Relevant for:** Comparative genomics, variant interpretation, ortholog discovery, and genomic feature annotation.

**3. NCBI BLAST MCP**
- **Repo:** github.com/bio-mcp/bio-mcp-blast
- **What it does:** Sequence similarity search via NCBI BLAST (nucleotide and protein searches).
- **Relevant for:** Core bioinformatics workflow; essential for homology searches and sequence alignment.

### Literature & Knowledge Integration

**4. PubMed MCP**
- **Repo:** Multiple implementations (jackkuo666, cyanheads, or via Anthropic Life Sciences)
- **What it does:** Search and retrieve biomedical literature via NCBI E-utilities; abstract retrieval, citation tracking.
- **Relevant for:** Literature review, hypothesis generation, contextualization of findings in published work.

**5. BioMCP**
- **Repo:** github.com/genomoncology/biomcp
- **What it does:** Integrated access to PubMed, clinical trials, genomic variants, Ensembl, and PDB in a single interface.
- **Relevant for:** All-in-one knowledge integration; useful when cross-referencing multiple data sources during analysis.

### Pathways & Metabolism

**6. Reactome MCP Server**
- **Repo:** github.com/Augmented-Nature/Reactome-MCP-Server
- **What it does:** 8 tools for pathway search, gene-to-pathway mapping, and reaction data retrieval.
- **Relevant for:** Metabolic pathway analysis, systems biology workflows, and functional genomics interpretation.

### Gene Expression & Omics

**7. GEO MCP**
- **Repo:** github.com/MCPmed/GEOmcp
- **What it does:** Access Gene Expression Omnibus (GEO) datasets; search and retrieve transcriptomic and other high-throughput data.
- **Relevant for:** Comparative expression analysis, data mining from public repositories, and benchmarking datasets.

### Protein Structure & Chemistry

**8. PDB/ChEMBL MCP**
- **Repo:** github.com/dogeplusplus/bio-agents-mcp
- **What it does:** Access to Protein Data Bank (3D structures) and ChEMBL (chemical compounds and drug properties).
- **Relevant for:** Structural biology, protein-ligand interaction analysis, and drug discovery workflows.

### Environmental & Earth Science

**9. Google Earth Engine MCP**
- **Search:** Current implementations available on GitHub and MCP registries
- **What it does:** Remote sensing data access, satellite imagery analysis, and geospatial processing.
- **Relevant for:** Environmental sampling site characterization, microbiome field data integration, and ecosystem-level studies.

### General Purpose (Useful for Everyone)

**10. Filesystem MCP**
- **Repo:** github.com/modelcontextprotocol/servers
- **What it does:** Safe file operations with access controls (read, write, list directories).
- **Relevant for:** Batch processing local data, managing large sequence files, and organizing analysis outputs.

**11. Git MCP**
- **Repo:** github.com/modelcontextprotocol/servers
- **What it does:** Read, search, and analyze git repositories; commit history, blame, diff operations.
- **Relevant for:** Code review, repository exploration, collaborative analysis workflows, and version tracking.

### From Anthropic Life Sciences Marketplace

**PubMed MCP**
- Search biomedical literature directly within Claude.

**Single-Cell RNA-seq QC Skill**
- Automated quality control pipelines for scRNA-seq data (cell filtering, doublet detection, ambient RNA removal).

**Nextflow Development Skill**
- Run nf-core pipelines including rnaseq, sarek (variant calling), and atacseq workflows.

**scvi-tools Skill**
- Deep learning frameworks for single-cell omics analysis, including batch correction and differential expression.

---

## Section 3: Installing an MCP Server

Quick reference for installing any MCP from GitHub. For full setup instructions, see workflow-guide.md.

### Basic Installation Steps

```bash
# 1. Clone the repository
git clone https://github.com/someorg/some-mcp-server.git
cd some-mcp-server

# 2. Install dependencies
# Check the README for specific requirements; typically one of:
pip install -e .
# or
uv pip install -e .

# 3. Register with Claude
claude mcp add --scope user server-name python -m some_mcp_server
# Or if the server has a standalone script:
claude mcp add --scope user server-name python /path/to/server.py

# 4. Verify
claude mcp list
```

### Managing Servers

```bash
# List registered servers
claude mcp list

# Remove a server
claude mcp remove --scope user server-name
```

### Best Practices

- Always check the MCP's README for specific installation requirements and dependencies.
- Test the MCP server locally before registering (`python server.py` should start without errors).
- Use `--scope user` to make servers available across all projects.
- Keep MCPs in a dedicated directory on your machine (e.g., `~/mcp-servers/`) or install skill+MCP combos to `~/.claude/skills/`.
- Document any custom configuration or API keys required in your lab's internal documentation.

---

## Finding More Resources

- **GitHub Search:** Use keywords like "biology MCP", "genomics MCP", "bioinformatics MCP", "microbiology MCP"
- **Awesome Lists:** Check GitHub's awesome-* lists for curated bioinformatics tools and integrations
- **Anthropic Documentation:** Visit docs.anthropic.com for the latest on MCP and skills ecosystem

---

**Last Updated:** February 2026

For questions or to suggest additional MCPs and skills, please open an issue or discussion in your lab's internal documentation repository.
