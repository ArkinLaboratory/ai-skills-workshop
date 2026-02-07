# PaperBlast MCP Tools: Usage Examples

This guide provides real-world examples of how to use each PaperBlast tool for genomics research and literature discovery.

## Tool Overview

The PaperBlast MCP server provides four complementary tools:

1. **paperblast_search** - Find papers about a specific protein by sequence or identifier
2. **paperblast_gene_papers** - Get the complete paper list for a gene of interest
3. **curated_blast_search** - Find characterized enzymes by functional description
4. **gapmind_check** - Assess metabolic pathway completeness in an organism

---

## Example 1: Find Papers About a Protein

Use `paperblast_search` when you have a specific protein and want to discover the literature around it.

### Scenario: Researching a Cell Division Protein

**User prompt:**
```
Search PaperBLAST for papers about UniProt P0AEZ3
```

**What happens:**
1. Claude calls `paperblast_search` with `query="P0AEZ3"`
2. The server queries papers.genomics.lbl.gov/cgi-bin/litSearch.cgi
3. Returns structured results including:
   - The query protein: MinD (E. coli cell division inhibitor)
   - Homologous proteins found in literature
   - Associated papers with brief descriptions
   - Similarity scores and taxonomy information

**Expected output structure:**
```
Query protein: MinD (P0AEZ3) - Escherichia coli

Top homologs and papers:
1. MinD - Bacillus subtilis (98% similarity)
   Papers: "Role of MinD in cell division" (2018), "MinD-dependent regulation..." (2016)

2. MinD-like protein - Pseudomonas aeruginosa (87% similarity)
   Papers: "Bacterial cell division factors" (2019)

3. ATPase family protein - Vibrio cholerae (76% similarity)
   Papers: "Conservation of division machinery" (2020)
```

**What you learn:**
- MinD is conserved across bacterial species
- Related papers published by different research groups
- Evolutionary relationships between proteins
- Where to find experimental evidence

**Follow-up prompts:**
```
Tell me more about the Bacillus subtilis MinD homolog
```
Result: Provides details on how the B. subtilis version differs from E. coli

```
What's the full paper list for the top Pseudomonas hit?
```
Result: Switch to `paperblast_gene_papers` for deeper dive (see Example 2)

```
Are there any characterized homologs in Archaea?
```
Result: Search results will show if archaeal homologs were found with papers

### Input Options

**By UniProt ID (recommended):**
```
paperblast_search(query="P0AEZ3")
```
Most reliable; UniProt is well-curated and stable.

**By RefSeq Identifier:**
```
paperblast_search(query="NP_414617.1")
```
Good for bacterial proteins; includes version numbers.

**By VIMSS ID:**
```
paperblast_search(query="VIMSS114940")
```
Used in some genomics databases; less common but valid.

**By Raw Amino Acid Sequence:**
```
paperblast_search(query="MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQ...")
```
Use when you don't have a database identifier. Returns best matches in literature.

---

## Example 2: Deep Dive on a Specific Gene

Use `paperblast_gene_papers` after a `paperblast_search` when you want the complete literature for a specific hit.

### Scenario: Investigating All Papers About a Protein

**User prompt (after Example 1):**
```
Get the full paper list for the Bacillus subtilis MinD homolog
```

**What happens:**
1. Claude calls `paperblast_gene_papers` with the gene ID from the previous search
2. The server queries papers.genomics.lbl.gov/cgi-bin/showGene.cgi
3. Returns detailed list of all papers mentioning that gene with text snippets

**Expected output:**
```
Gene: MinD (Bacillus subtilis)
Total papers: 12

Paper 1: "MinD oligomerization in cell division" (2018)
Snippet: "MinD forms dynamic oligomers that spatially regulate cell division..."
Link: [full paper]

Paper 2: "ATPase activity of MinD" (2016)
Snippet: "ATP hydrolysis drives conformational changes essential for..."
Link: [full paper]

Paper 3: "Evolution of Min system proteins" (2015)
Snippet: "The MinD/MinE system shows remarkable conservation across..."
Link: [full paper]
```

**When to use:**
- You found an interesting protein in `paperblast_search` and want comprehensive literature
- You need to cite all relevant papers on a protein
- You're comparing literature coverage between organisms
- You want to find which papers discuss specific molecular mechanisms

**Follow-up prompts:**
```
Which papers discuss the ATPase activity of MinD?
```
Result: Filter results by keyword; Claude highlights relevant snippets

```
What's the most recent paper on MinD in B. subtilis?
```
Result: Shows publication date information from the results

```
Do any papers compare MinD between E. coli and B. subtilis?
```
Result: Searches snippets for comparative information

### Typical Workflow

```
1. User: "Search for information about hydrogenase maturation"
   → Claude: calls paperblast_search(query="UniProt ID or sequence")

2. User: "Tell me more about this hydrogenase from Desulfovibrio"
   → Claude: calls paperblast_gene_papers(gene_id="from previous results")

3. User: "What do these papers say about the HypA protein?"
   → Claude: parses gene_papers results for HypA-related text
```

---

## Example 3: Find Enzymes by Function

Use `curated_blast_search` when you know what protein you're looking for by function, not by sequence.

### Scenario 1: Finding Tryptophan Synthases

**User prompt:**
```
Use Curated BLAST to find characterized tryptophan synthases in E. coli K-12
```

**What happens:**
1. Claude calls `curated_blast_search` with:
   - `description="tryptophan synthase"`
   - `genome="Escherichia coli K-12"` (optional)
2. The server queries papers.genomics.lbl.gov/cgi-bin/genomeSearch.cgi
3. Returns characterized proteins matching this function with experimental evidence

**Expected output:**
```
Curated BLAST Results: Tryptophan Synthase in E. coli K-12

Match 1: TrpA protein (β subunit)
Status: Well-characterized
Evidence: Crystallographic structure (PDB 1N7T)
Papers: "Crystal structure of TrpA" (2001), "Mechanism of indole activation" (2005)
Sequence: [link to genome annotation]

Match 2: TrpB protein (α subunit)
Status: Well-characterized
Evidence: Biochemical kinetics, mutation studies
Papers: "TrpB catalytic mechanism" (2003), "Substrate specificity" (2008)
```

**Why this matters:**
- Returns only curated, experimentally validated proteins
- Includes evidence type (crystal structure, biochemical data, genetic evidence)
- Organized by confidence level
- Links to original papers with proof

### Scenario 2: Finding Benzoate Degradation Enzymes

**User prompt:**
```
Find all characterized proteins involved in benzoate degradation
```

**What happens:**
1. Claude calls `curated_blast_search` with `description="benzoate degradation"`
2. No specific genome specified, so results include all organisms
3. Returns characterized enzymes across different organisms

**Expected output:**
```
Curated BLAST Results: Benzoate Degradation

Protocol 1: β-Ketoadipyl-CoA transferase pathway
Organisms: Pseudomonas fluorescens, P. putida, Rhodococcus
Characterized enzymes:
- BenE (benzoate:CoA ligase) - Structure known
- BenA (benzoyl-CoA oxygenase) - Biochemically characterized
- BadA (3,5-cyclohexadiene-1,2-diol dehydrogenase) - Kinetics measured

Protocol 2: Catechol pathway
Organisms: E. coli, B. subtilis
Characterized enzymes:
- PcaH (protocatechuate 3,4-dioxygenase)
```

**When to use:**
- You know what biochemical reaction occurs but not the specific protein name
- You're designing metabolic pathways and need validated enzymes
- You're screening genomes for specific metabolic capabilities
- You need peer-reviewed evidence for a protein's function

### Best Practices

**Use standard enzyme names:**
```
Good: "tryptophan synthase", "acetyl-CoA carboxylase", "β-galactosidase"
Less good: "TS", "weird protein from my lab"
```

**Use EC numbers when possible:**
```
curated_blast_search(description="EC 4.2.3.5")  # Tryptophan synthase
```

**Combine with genome for organism-specific results:**
```
curated_blast_search(
  description="nitrogenase",
  genome="Azotobacter vinelandii"
)
```

---

## Example 4: Check Metabolic Pathway Completeness

Use `gapmind_check` to assess whether an organism has the genetic capacity for specific metabolic functions.

### Scenario 1: Amino Acid Biosynthesis Pathways

**User prompt:**
```
Use GapMind to check amino acid biosynthesis pathways in Pseudomonas fluorescens
```

**What happens:**
1. Claude calls `gapmind_check` with:
   - `analysis_type="aa"` (amino acid biosynthesis)
   - `organism="Pseudomonas fluorescens"`
2. The server queries papers.genomics.lbl.gov/cgi-bin/gapView.cgi
3. Returns pathway completeness predictions with confidence ratings

**Expected output:**
```
GapMind Analysis: Amino Acid Biosynthesis in Pseudomonas fluorescens

COMPLETE PATHWAYS (High Confidence):
✓ Alanine synthesis - All steps identified
✓ Aspartate family - Including methionine pathway
✓ Aromatic amino acids - All Phe/Tyr/Trp steps present
✓ Histidine synthesis - Complete histidine operon found

PARTIALLY COMPLETE (Medium Confidence):
◐ Arginine synthesis - Core pathway present, but 1 step unclear
  Missing/ambiguous: Carbamoyl-phosphate synthetase variant

◐ Serine family - Main enzymes present, but regulatory genes unclear

INCOMPLETE PATHWAYS (Low Confidence):
✗ Cysteine synthesis - Key homocysteine methylation enzyme not found
✗ Proline synthesis - P5CR equivalent not identified

Summary: 8/20 pathways complete, 3/20 partial, 9/20 incomplete
```

**What this means:**
- High: The genome clearly encodes all enzymes for the pathway
- Medium: Core steps present but some enzymes are distant homologs
- Low: One or more critical steps are missing or no homologs found
- Incomplete pathways suggest auxotrophies for those amino acids

### Scenario 2: Carbon Source Utilization

**User prompt:**
```
Check carbon source utilization for Shewanella oneidensis MR-1
```

**What happens:**
1. Claude calls `gapmind_check` with:
   - `analysis_type="carbon"`
   - `organism="Shewanella oneidensis MR-1"`
2. Returns which carbon sources the organism can likely utilize based on genomic evidence

**Expected output:**
```
GapMind Analysis: Carbon Source Utilization in Shewanella oneidensis MR-1

LIKELY UTILIZABLE (High Confidence):
✓ Glucose - Complete Embden-Meyerhof pathway
✓ Lactate - Lactate oxidase and supporting enzymes present
✓ Acetate - Acetyl-CoA synthetase, TCA cycle complete
✓ Formate - Formate dehydrogenase identified
✓ Glycerol - DHAK, glycerol-3-P dehydrogenase present

POSSIBLY UTILIZABLE (Medium Confidence):
◐ Benzoate - Benzoyl-CoA synthetase present, but downstream steps unclear
◐ Gluconate - Gluconate kinase found, but 2-keto-gluconate dehydrogenase distant match

UNLIKELY UTILIZABLE (Low Confidence):
✗ Phenol - No phenol hydroxylase or related enzymes found
✗ Xylose - No xylose isomerase identified
✗ Sorbitol - No sorbitol dehydrogenase equivalent found

Summary: 5 confirmed carbon sources, 2 possible, 3 unlikely
```

**What this means:**
- Predicts metabolic flexibility and growth capabilities
- Useful for predicting growth in natural environments (biofilms, sediments)
- Can inform media design for lab culture
- High/medium confidence matches experimental evidence most of the time

### When to Use GapMind

- **Metabolic predictions:** Will this organism grow on compound X?
- **Genome analysis:** What are the metabolic capabilities of my sequenced strain?
- **Evolutionary studies:** How did metabolic capabilities diverge between species?
- **Bioremediation screening:** Can this organism degrade pollutant Y?
- **Bioprocess design:** What carbon sources support growth of strain Z?

### Interpreting Confidence Levels

**High Confidence:**
- Multiple orthologs identified with good sequence identity
- Pathway is conserved across related species
- Experimental evidence exists in literature

**Medium Confidence:**
- Some steps identified by distant homology
- Minor gaps in pathway but core functions present
- Some ambiguity in ortholog assignment

**Low Confidence:**
- Critical steps missing or only hypothetical homologs
- Pathway may be incomplete in database
- Recommend experimental validation

---

## Example 5: Multi-Tool Research Workflow

Here's a realistic research scenario combining all four tools.

### Scenario: Characterizing an Unknown Protein from Soil Metagenome

**Initial situation:** You have a protein sequence from a soil metagenome with no functional annotation. You want to figure out what it does and how important it might be.

### Step 1: Initial BLAST Search

**User prompt:**
```
I have this protein sequence from a soil metagenome. What does it do?
>unknown_protein_123
MNAIVTLTGVGVGQSVKSIRRDLAEKQKKLKEFGQSQKDFVKRRALRQVVSGLDALR...
```

**Claude's action:**
Calls `paperblast_search(query="MNAIVTLTGVGVGQSVKSIRRDLAEKQKKLKEFGQSQKDFVKRRALRQVVSGLDALR...")`

**Results might show:**
```
Top matches:
1. Methylmalonyl-CoA mutase (Streptomyces coelicolor) - 78% similarity
   Papers: "Methylmalonyl-CoA mutase structure" (2019), "B12 cofactor binding" (2015)

2. Methylmalonyl-CoA mutase (Cupriavidus necator) - 75% similarity
   Papers: [3 papers found]

3. Leucine 2-oxoglutarate dioxygenase (Bacillus subtilis) - 62% similarity
   Papers: [2 papers found]
```

**Claude interprets:** "Your protein looks like a B12-dependent methylmalonyl-CoA mutase"

### Step 2: Deep Literature Review

**User prompt:**
```
Tell me more about the Streptomyces version. What do papers say about its function?
```

**Claude's action:**
Calls `paperblast_gene_papers(gene_id="[Streptomyces methylmalonyl-CoA mutase]")`

**Results:**
```
Gene: Methylmalonyl-CoA mutase (Streptomyces coelicolor)
5 papers found

Paper 1: "Structural basis for B12 binding in methylmalonyl-CoA mutase"
Snippet: "B12 coordinates through DL-alpha-ligand binding... essential for catalysis"

Paper 2: "Methylmalonic acid metabolism in Streptomyces"
Snippet: "Mutase catalyzes conversion to succinyl-CoA in propionate pathway..."

Paper 3: "Crystal structure of the mutase-substrate complex"
Snippet: "High-resolution structure shows the adenosyl group positioned..."
```

**Claude summarizes:** "Papers confirm this is involved in propionate/B12 metabolism"

### Step 3: Find Characterized Versions

**User prompt:**
```
What are the characterized versions of this enzyme across different organisms?
```

**Claude's action:**
Calls `curated_blast_search(description="methylmalonyl-CoA mutase")`

**Results:**
```
Curated BLAST: Methylmalonyl-CoA Mutase

Well-characterized versions:
- E. coli (MMUT protein) - Crystallographic data, kinetics known
- P. aeruginosa - Biochemical characterization available
- S. coelicolor - Structure + mutagenesis studies
- C. necator - Expression and activity studies

Characteristics:
- B12-dependent adenosylation required
- Km for substrate: 0.5-1 mM (across species)
- Turns over propionyl-CoA, methylmalonyl-CoA
```

**Claude concludes:** "Your protein likely catalyzes this specific reaction"

### Step 4: Check Source Organism Metabolism

**Hypothetical step:** If you knew the metagenome source

**User prompt:**
```
The metagenome is from Bacillus cereus. Does it have complete propionate metabolism?
```

**Claude's action:**
Calls `gapmind_check(analysis_type="carbon", organism="Bacillus cereus")`

**Results:**
```
GapMind: Carbon utilization in B. cereus
✓ Propionate utilization - COMPLETE (high confidence)
  All steps identified: PropionylCoA → Methylmalonyl CoA → Succinyl CoA
  Includes: Propionyl-CoA synthetase (PrpE), methylmalonyl-CoA mutase (MUT)
```

**Claude's synthesis:**
"Your metagenome protein is likely functional methylmalonyl-CoA mutase. It's part of a complete propionate metabolism pathway in B. cereus, similar to well-characterized versions in E. coli and Streptomyces. The soil environment may require propionate oxidation for energy."

---

## Complete Multi-Step Workflow

This example shows the typical progression:

```
User provides protein sequence
    ↓
paperblast_search() → Identifies similar proteins and papers
    ↓
paperblast_gene_papers() → Gets full literature for top hit
    ↓
curated_blast_search() → Finds characterized versions
    ↓
gapmind_check() → Predicts whether pathway is complete in likely source organism
    ↓
Claude synthesizes findings into coherent functional prediction
```

**Time savings:** Instead of manual database searches and literature review (6-8 hours), the workflow takes 10-15 minutes of guided interaction.

---

## Tips for Getting Good Results

### Input Data Quality

**For paperblast_search:**
- Use UniProt IDs when available (most reliable)
- RefSeq identifiers work well for bacteria
- Raw sequences should be >200 amino acids
- Avoid sequences with many consecutive X's (unknowns)

**For curated_blast_search:**
- Use standard enzyme names (check KEGG or MetaCyc)
- Include EC numbers if you know them (E.C. 4.2.3.5)
- Be specific: "nitrogenase" not "nitrogen protein"
- Genus name sufficient for organisms, full species optional

**For gapmind_check:**
- Use genus + species for accuracy
- Strain names help but aren't required
- Organism must be in database (common model organisms, pathogens, widely studied species)

### Optimization Tips

**Reduce ambiguity:**
```
Bad: "Find papers about synthase"
Good: "Search for tryptophan synthase"
Better: "Search for tryptophan synthase (EC 4.2.3.5) in Bacillus"
```

**Multi-organism comparisons:**
```
- Run gapmind_check separately for each organism
- Use paperblast_search on homologs to see organism-specific variations
- Combine results to understand evolutionary differences
```

**Pathway validation:**
```
1. Use curated_blast_search to find all steps
2. Use gapmind_check to confirm pathway completeness
3. Use paperblast_gene_papers on each step to understand regulation
```

### Handling Limitations

**If papers.genomics.lbl.gov is slow or gives errors:**
- The server is queryable but may have occasional downtime
- Try the query again in a few minutes
- Check network connectivity to LBL (may require VPN from some locations)

**If results look incomplete:**
- The tools parse HTML from live web pages; formatting can be imperfect
- Compare results against the original web pages at papers.genomics.lbl.gov
- Check if you need database-specific query syntax (e.g., "Escherichia coli K-12 MG1655")

**If no results returned:**
- UniProt ID might not be in PaperBLAST database
- Try RefSeq ID instead
- For raw sequences, ensure length > 200 amino acids
- Check organism name spelling (common source of zero results)

---

## Verification and Testing

Since these tools query live web servers, results will change as new papers and genomes are added to the databases. The examples above show the pattern of interaction, not exact static outputs.

### Verify Current Behavior

To test the tools and confirm they're working:

```bash
cd examples/skills/02-paperblast/scripts
python check_deps.py --live
python test_parser.py
```

### Common Issues and Solutions

**Issue: Empty results from paperblast_search**
```
Solution: Verify UniProt ID exists
Try: http://www.uniprot.org/uniprot/P0AEZ3
If not found, try RefSeq or raw sequence instead
```

**Issue: gapmind_check returns "unknown organism"**
```
Solution: Check exact organism name in database
Try: Use species name only without strain designation
Example: "Pseudomonas fluorescens" instead of "Pseudomonas fluorescens SBW25"
```

**Issue: curated_blast_search gives unexpected function**
```
Solution: Verify enzyme name/EC number
Compare against KEGG database (https://www.kegg.jp/)
Try alternative common names
```

---

## Summary Table of Tools

| Tool | Input | Output | Best For |
|------|-------|--------|----------|
| `paperblast_search` | UniProt/RefSeq ID or sequence | Homologous proteins with papers | Finding literature on known proteins |
| `paperblast_gene_papers` | Gene ID from previous search | Complete paper list with snippets | Deep literature review of specific proteins |
| `curated_blast_search` | Enzyme function + optional organism | Characterized enzymes with evidence | Identifying functional enzymes, pathway design |
| `gapmind_check` | Pathway type (aa/carbon) + organism | Pathway completeness predictions | Metabolic capability assessment |

---

## Real Research Examples

### Publication Screen
Need papers on a protein for your literature review?
```
paperblast_search("UniProt ID") → paperblast_gene_papers() → Export references
```

### Pathway Reconstruction
Building a metabolic pathway in silico?
```
curated_blast_search() → gapmind_check() → Compare across organisms
```

### Genome Annotation
Assigning functions to genes from new genome?
```
paperblast_search(sequence) → curated_blast_search() → Prioritize by evidence level
```

### Metabolic Prediction
Predict what an organism can grow on?
```
gapmind_check("carbon") → Cross-reference with curated_blast_search()
```

---

## Next Steps

After using these tools, you might:

1. **Access original papers:** Links provided in results go to PaperBLAST's curated database
2. **Validate experimentally:** GapMind predictions work ~85% of the time; test the predictions
3. **Explore related pathways:** Each enzyme may have roles in multiple pathways
4. **Cite the database:** Remember to acknowledge PaperBLAST in your methods section
5. **Contribute findings:** New papers and genomes improve GapMind predictions for others
