# PaperBLAST Skill Design Rationale: A Real-World Case Study

## 1. Overview

The PaperBLAST skill wraps three literature search and metabolic prediction tools from Morgan Price's suite at papers.genomics.lbl.gov: PaperBLAST (protein sequence search with literature), Curated BLAST (function-based homolog search), and GapMind (metabolic gap analysis), exposed via five MCP tools. The skill demonstrates a common and challenging pattern in scientific software: integrating legacy web tools (Perl CGI endpoints returning HTML, no formal JSON API) into Claude's structured tool ecosystem via an MCP server.

This is not a toy example. Real researchers in computational biology use these tools daily. The skill must balance fidelity to the tools' actual capabilities (including their quirks and limitations) with Claude's need for clear, unambiguous instructions on when and how to invoke them.

---

## 2. Anatomy: Frontmatter

The YAML frontmatter is Claude's first and often only impression of a skill if it's loaded as metadata only.

### `name: paperblast`

**Assessment: Good, but inconsistent with style guide recommendation.**

The name is short, lowercase, and immediately recognizable. However, the skill-authoring guide recommends gerund forms (e.g., `searching-paperblast` or `querying-paperblast`) to clarify that this is an action, not an object. The imperative form in the SKILL.md body ("Search PaperBLAST...") reinforces this inconsistency.

In practice, this matters less than it should. Claude infers intent from context, and `paperblast` is unambiguous. But for consistency and discoverability: consider renaming to `searching-paperblast` in future versions. The trade-off is brevity vs. clarity.

**Recommendation:** Acceptable as-is; consider `searching-paperblast` for consistency with workshop style.

### `description:` Field

**Assessment: Strong entry point, but minor voice inconsistency and room for expansion.**

Let's analyze structure:

```yaml
description: >
  Search PaperBLAST for literature about proteins, find characterized proteins
  by function via Curated BLAST, and check metabolic pathway gaps with GapMind.
  Use when: (1) user asks about papers or literature for a protein or gene,
  (2) user wants to find characterized proteins matching a functional description,
  (3) user asks about amino acid biosynthesis or carbon source utilization
  capability of an organism, (4) user mentions PaperBLAST, GapMind, or Curated BLAST,
  (5) user wants to annotate hypothetical proteins using literature evidence.
  Wraps papers.genomics.lbl.gov CGI tools via MCP server.
```

**Voice:** Strictly, the guide recommends third person passive ("Searches PaperBLAST..." or "Provides literature searches via PaperBLAST..."). This description uses imperative ("Search PaperBLAST..."), which is slightly conversational but not technically wrong. It matches Claude's natural action-oriented language in practice.

**Trigger conditions:** The "Use when:" block is excellent. Five explicit conditions:
1. Papers/literature for a protein or gene
2. Find characterized proteins by functional description
3. Amino acid biosynthesis or carbon source utilization of an organism
4. User mentions the tool names explicitly
5. Annotate hypothetical proteins with literature evidence

This is thorough trigger coverage. Condition (4) is defensive — if a user explicitly asks for GapMind, the skill should activate even if they haven't described their actual need. Conditions (1), (2), (3), (5) cover the biological use cases. Good mapping.

**Keyword density:** "papers", "literature", "protein", "gene", "characterized proteins", "functional description", "amino acid biosynthesis", "carbon source", "GapMind", "Curated BLAST", "PaperBLAST", "metabolic pathway", "hypothetical proteins", "annotate". These are the keywords Claude will use for relevance matching. Dense and appropriate.

**Implementation note:** The final sentence ("Wraps papers.genomics.lbl.gov CGI tools via MCP server") tells Claude what architecture to expect. This is debatable — it's implementation detail, not user-facing knowledge. But it does signal to Claude that results may be parsed from HTML, which is helpful context if results look odd. Keep it.

**Character count:** ~500 / 1024 max, leaving room for expansion if additional patterns emerge.

### Missing Fields

**`allowed-tools` or `disable-model-invocation`:** Not present, and appropriately so. This skill wraps an MCP server. Claude doesn't invoke tools directly from the SKILL.md; instead, the MCP server exposes tools and Claude invokes them via the MCP protocol. No `allowed-tools` is needed because the MCP itself controls which tools are available. `disable-model-invocation` isn't needed because we WANT Claude to call these tools when appropriate (it's not a display-only reference skill).

**`version`:** Not present. Best practice for scientific tools is to include a version string. Recommended addition:

```yaml
version: "1.0"
```

This makes it easy for users to track when they have an outdated skill.

---

## 3. Anatomy: Tool Reference Table

Immediately after the main heading, a table introduces the five available MCP tools:

```
| Tool | Use when | Input | Returns |
|------|----------|-------|---------|
| `paperblast_search` | Finding papers about a protein | Sequence or identifier + `max_hits` (default 25) | `PaperBlastResults` |
| `paperblast_gene_papers` | Drilling into a specific hit | `detail_id` from prior search hit | `GenePapersResults` |
| `curated_blast_search` | Finding characterized proteins by function | Functional description + optional genome | `CuratedBlastResults` |
| `gapmind_check` | Checking metabolic completeness | Analysis type (aa/carbon) + organism or org_id | `GapMindResults` or `GapMindOrganismIndex` |
| `gapmind_list_organisms` | Listing available GapMind organisms | Analysis type (aa/carbon) | `GapMindOrganismIndex` |
```

**Assessment: Excellent. This is the core of skill usability.**

This table encodes four critical pieces of information:
- **Tool names** (exact strings for invocation): `paperblast_search`, `paperblast_gene_papers`, `curated_blast_search`, `gapmind_check`, `gapmind_list_organisms`
- **Decision logic**: When should Claude pick each tool?
- **Input format**: What arguments does each tool expect?
- **Return types**: What structured output to expect

Without this table, Claude would see from the MCP registration that these tools exist, but would have to infer from tool schemas alone when to use which tool. That inference would be mediocre. The table gives Claude explicit decision rules.

**Strengths:**
- "Use when" column translates scenarios to tools (e.g., "Finding papers about a protein" → `paperblast_search`)
- Input column tells Claude what constitutes good input (e.g., "Sequence or identifier", not just "string")
- Compact format fits in the readable portion of SKILL.md
- Returns column is a major improvement. It tells Claude exactly what structured output to expect from each tool, enabling precise follow-up queries and programmatic filtering (e.g., "return only hits with >80% identity")

**Room for improvement:**
- No information about required vs. optional parameters (all are implied as required in the current table, though `max_hits` is shown as optional)
- No mention of what happens when a tool fails or returns no results (see section 4 for related critique)

---

## 4. Anatomy: Workflow Patterns

Four patterns, from simple to complex:

### Pattern 1: Annotate a hypothetical protein
```
1. `paperblast_search` with the protein sequence
2. Review hits — check identity % and paper relevance
3. For promising hits, `paperblast_gene_papers` to get the full literature
4. Synthesize annotation from convergent evidence
```

**Assessment: Clear and actionable.** This is the main use case. The workflow is tight: search, filter, drill, synthesize. Step 2 ("Review hits...") acknowledges that Claude needs to make judgment calls about which results are biologically relevant, not just pull the top hit.

**Issue:** No error handling. What if `paperblast_search` returns no hits with >30% identity? Should Claude suggest trying:
- A shorter subsequence?
- A database of only the target organism instead of all bacteria?
- `curated_blast_search` with a functional guess if one can be made?

This is domain-specific resilience that the workflow doesn't capture.

### Pattern 2: Find functional homologs in a genome
```
1. `curated_blast_search` with a functional description (e.g., "acetaldehyde dehydrogenase")
2. Optionally specify genome_db="NCBI" and genome_id for a specific organism
3. Results show experimentally-characterized proteins with homologs in the target genome
```

**Assessment: Good, with optional parameters clearly flagged.** Curated BLAST is the complementary tool to PaperBLAST: instead of "I have a sequence, find papers," it's "I want a function, find characterized examples." The optional genome filtering is important — without it, the tool returns homologs across all available genomes.

**Issue:** The parameter names (`genome_db="NCBI"`, `genome_id`) are tool-specific and should ideally be documented in the tool schema, not here. But since they're not documented in the SKILL.md as parameter schemas (only in the table's "Input" column), repeating them here is helpful.

### Pattern 3: Predict metabolic capability
```
1. `gapmind_list_organisms` (or `gapmind_check` with no organism) to browse available organisms
2. `gapmind_check` with `organism="Pseudomonas fluorescens"` — fuzzy-matches against the index
3. Or use `org_id` directly: `gapmind_check(org_id="FitnessBrowser__pseudo1_N1B4")`
4. High-confidence = pathway complete; low = missing steps (gaps)
```

**Assessment: Solid pattern that resolves the organism ID issue.** The pattern shows the new two-step GapMind flow: first browse the organism index, then query with fuzzy-matched organism names or exact org IDs. This overcomes the previous limitation where free-text organism names would fail.

**Strengths:**
- Two clear pathways: browse-then-query for discovery, or direct org_id for known identifiers
- Fuzzy matching handles common naming variations
- GapMindOrganismIndex provides the full catalog of available organisms

**Interpretation guidance:**
- High-confidence indicates the organism likely has a complete pathway
- Low-confidence indicates missing steps; use the gap descriptions to identify which enzymes are predicted to be absent
- Present results in context: "Can synthesize amino acids from X, but missing ability to synthesize Y (enzyme Z is absent)."

### Pattern 4: Cross-tool enrichment (PROTECT example)
```
1. Get organism list from KBase metagenome analysis
2. For each organism of interest, `gapmind_check` to predict metabolism
3. For key proteins, `paperblast_search` to find literature evidence
4. `curated_blast_search` to identify characterized homologs
```

**Assessment: Realistic integration example.** This pattern shows a real research workflow (PROTECT is an actual Arkin Lab project) where multiple tools are combined. It demonstrates that the skill isn't just for isolated queries but for research pipelines.

**Issue:** No mention of scaling. If there are 50 organisms of interest, steps 2-4 could generate 150+ tool calls. No guidance on:
- When to parallelize vs. serialize?
- When to sample (e.g., "top 10 organisms by abundance")?
- How to handle tool rate limiting or timeouts?

This is inherent to cross-tool patterns — the skill's scope is tool invocation, not research methodology. But a brief note would help:

```
Note: Scaling across many organisms may require batching tool calls
or prioritizing by abundance. See references/scaling.md for guidelines.
```

---

## 5. Anatomy: Query Tips

This section teaches Claude domain-specific input formatting that wouldn't be obvious from tool schemas alone:

```
- **Protein identifiers** work better than sequences for quick lookups:
  UniProt (P0AEZ3), RefSeq (WP_003246543.1), VIMSS locus tags (VIMSS14484)
- **Raw sequences** trigger a BLAST search (slower, ~10-30s) but work for
  novel proteins with no known identifier
- **Curated BLAST queries** should be functional descriptions, not gene names.
  Good: "alcohol dehydrogenase", "two-component sensor kinase"
  Bad: "acrB", "SO_1234"
- **GapMind organism names** are fuzzy-matched against a pre-computed index. Use `gapmind_list_organisms` to browse available organisms, or pass organism names to `gapmind_check` which will match them automatically. Exact org IDs (e.g., `FitnessBrowser__pseudo1_N1B4`) are also supported.
```

**Assessment: Essential and well-structured.**

The "Good/Bad" examples for Curated BLAST are particularly valuable. Claude could theoretically infer that functional descriptions are better than gene names, but the explicit examples make it clear and prevent the common mistake of searching for a locus tag.

**Strengths:**
- Concrete examples (P0AEZ3, WP_003246543.1, VIMSS14484, "alcohol dehydrogenase")
- Performance expectations (10-30s for BLAST) set correct expectations
- Hierarchical guidance: preferred input first, then fallbacks
- GapMind guidance is now implementation-accurate: fuzzy matching is available and `gapmind_list_organisms` provides browsing capability

**Status:** The GapMind organism naming guidance is now current-state rather than aspirational. The two-step flow and fuzzy matching resolve the previous limitation where free-text names would fail.

---

## 6. Anatomy: HTML Parsing Note

```
## HTML Parsing Note
These tools scrape HTML from CGI endpoints (no formal JSON API exists). The
HTML parsers in `scripts/paperblast_mcp.py` use heuristic pattern matching
and may need updates if the page structure changes. If results look wrong,
check the `search_url` or `detail_url` field in the output to verify against
the live web page.
```

**Assessment: Pragmatic and appropriate.**

Most skill documentation would never mention implementation details like "HTML scraping." But for an MCP wrapping legacy CGI tools, this note is valuable. It tells Claude:
1. Results might be fragile (if page structure changes)
2. To verify by checking the URL if results look odd
3. That `search_url` and `detail_url` fields are available for manual verification

This is especially important for scientific tools, where wrong results could influence research. Transparency about fragility builds trust.

**Recommendation:** Keep this. It's honest and practical.

---

## 7. Progressive Disclosure in Practice

The PaperBLAST skill and its supporting files demonstrate the three-level loading architecture recommended in the style guide.

**Level 1 (Metadata):** Claude loads the frontmatter on skill activation:
```yaml
name: paperblast
description: >
  Search PaperBLAST for literature about proteins, find characterized proteins
  by function via Curated BLAST, and check metabolic pathway gaps with GapMind.
  Use when: ...
```
Token cost: ~100 tokens. Decision: "Does this skill match the user's question?" If yes, proceed to Level 2.

**Level 2 (Body):** Claude loads the full SKILL.md (~128 lines, ~600-700 tokens):
- Tool reference table (decision logic) with Returns column
- Four workflow patterns (how to sequence tool calls), including the new two-step GapMind flow
- Query tips (domain-specific input formatting), with updated GapMind guidance
- HTML parsing note (why results might be fragile)
- Return Data Models section describing the 13 Pydantic output models

This is everything needed for most interactions. Claude never loads Level 3 for routine PaperBLAST queries.

**Level 3 (References):** The `references/setup.md` file and supporting documentation contain:
- Installation and configuration instructions (INSTALL.md)
- Testing and validation procedures (TESTING.md)
- How to extend the MCP with additional CGI tools
- Troubleshooting for specific error codes

This is only loaded if the user asks about setup, testing, or extending the skill — not during normal queries.

**Supporting files (scripts/):**
- `paperblast_mcp.py`: The actual MCP server. Claude doesn't read this; the Claude runtime loads it via the MCP protocol.
- `models.py`: Pydantic output models (13 total) defining the return types for all tools. Referenced in SKILL.md's Returns column.
- `check_deps.py`, `test_parser.py`: Utilities for humans, not for Claude.

**Why this matters:** By keeping Level 2 focused and Level 3 separate, the skill remains fast to load and easy to understand. Users who just want to search PaperBLAST don't have to wade through installation instructions.

---

## 8. The Skill + MCP Pairing: Complementary Division of Labor

The SKILL.md and `paperblast_mcp.py` serve distinct purposes and are incomplete without each other.

### SKILL.md: Domain Knowledge
- When to invoke each of the five tools
- What inputs produce good results (identifiers vs. sequences, functional descriptions)
- How to sequence tool calls (workflow patterns), including the two-step GapMind flow
- How to interpret results (GapMind confidence, identity percentages)
- What structured data models to expect from each tool (Returns column)
- Limitations and fragility (HTML parsing)

### MCP Server (paperblast_mcp.py): Mechanical Capability
- Construct HTTP requests to papers.genomics.lbl.gov
- Parse HTML responses using regex/heuristics
- Return structured data to Claude

### Why Both Are Necessary

**MCP without SKILL.md:** Claude sees five tools but lacks context. For example:
- When should it call `curated_blast_search` vs. `paperblast_search`?
- What does a good organism name look like for GapMind?
- How should results be presented to the user?

Claude would have to infer from tool descriptions alone, leading to suboptimal choices.

**SKILL.md without MCP:** Claude would have all the knowledge but couldn't execute. It would tell the user "I would search PaperBLAST if I could" but have no mechanism to do so.

**Both together:** Claude has both knowledge and capability, enabling sound decisions and reliable execution.

---

## 9. Known Issues and Planned Improvements

Being honest about limitations is essential for a living skill. The current implementation has several known issues worth documenting:

### Issue 1: Structured Data — RESOLVED

**Previous state:** The MCP returned parsed text strings with no machine-readable structure.

**Current state:** All tools now return structured JSON conforming to Pydantic output models defined in `scripts/models.py`. Thirteen models cover all tool outputs, including:
- `PaperBlastResults`
- `GenePapersResults`
- `CuratedBlastResults`
- `GapMindResults`
- `GapMindOrganismIndex`

This enables programmatic filtering (e.g., "show only hits with >80% identity"), downstream computation (e.g., sorting by E-value across multiple queries), and pipeline integration for batch operations.

### Issue 2: GapMind Organism ID — RESOLVED

**Previous state:** `gapmind_check` accepted free-text organism names but GapMind's backend requires pre-computed organism IDs. Most queries failed.

**Current state:** Two fixes implemented:
1. New `gapmind_list_organisms` tool fetches the full organism index for browsing
2. `gapmind_check` now fuzzy-matches organism names against the index internally
3. Users can also pass `org_id` directly for exact matches (e.g., `org_id="FitnessBrowser__pseudo1_N1B4"`)

The SKILL.md documents the two-step flow (browse then query) and query tips now accurately reflect the implementation. Users can pass organism names like "Escherichia coli" or "Pseudomonas fluorescens" to `gapmind_check` and they will be automatically matched against the available organisms in GapMind.

### Issue 3: No Fallback Guidance

**Current state:** If the `paperblast_mcp` server is down or returns errors, the skill has no fallback strategy.

**Problem:** In production, users might prefer to have Claude attempt a web fetch to papers.genomics.lbl.gov directly, parsing the HTML itself, rather than completely failing.

**Potential improvement:** Add a note in the workflow patterns:
```
If the MCP server is unavailable, Claude can still access PaperBLAST
by visiting papers.genomics.lbl.gov directly. However, this is slower
and less structured. Prefer the MCP when available.
```

**Status:** Nice-to-have, not critical.

### Issue 4: Description Voice Inconsistency

**Current state:** Description uses imperative ("Search PaperBLAST...") instead of third-person passive recommended in the style guide.

**Recommendation:** Minor. Change to:
```yaml
description: >
  Searches PaperBLAST for literature about proteins, finds characterized proteins
  by function via Curated BLAST, and checks metabolic pathway gaps with GapMind.
```

**Impact:** Negligible in practice, but improves consistency across the workshop.

---

## 10. Lessons for Building Your Own Skills

When you build a skill for your own tools or integrate external tools, apply what works here:

### 1. Description Is Your Elevator Pitch
The description field is loaded first and most frequently. Spend time on it:
- List 4-5 explicit trigger conditions so Claude loads the skill appropriately
- Include key terms users might search for
- Be specific about what the skill does, not what it's called

The PaperBLAST description succeeds here by naming tools, biological concepts, and trigger keywords.

### 2. Tool Reference Tables Are Non-Negotiable for MCP Skills
If your skill wraps an MCP with multiple tools, include a table that maps:
- Tool name → Exact invocation string
- Scenario → Best tool for that scenario
- Inputs → What makes a good input

Without this, Claude invokes tools semi-randomly and users get mediocre results.

### 3. Workflow Patterns Give Claude Decision Logic, Not Just Awareness
Listing available tools isn't enough. Encode the sequencing and decision rules:
- When should tool A precede tool B?
- Which tool results trigger a follow-up query?
- How do you combine results from multiple tools?

The four PaperBLAST patterns model this well.

### 4. Query Tips Teach Domain-Specific Input Formatting
Good schemas document parameter types (string, float, enum). But good skills document:
- What makes a good protein identifier vs. a bad one
- What format an organism name should take
- What performance to expect (slow BLAST vs. fast database lookup)
- Common mistakes and how to avoid them

Include concrete "Good/Bad" examples.

### 5. Use `references/` for Non-Critical Information
Keep the main SKILL.md tight (50-100 lines). Move to references/ anything that's needed only occasionally:
- Setup and installation
- Extension guides (how to add new tools)
- Troubleshooting (specific error codes and fixes)
- Scaling guidance (batching, rate limits)

This speeds up skill loading for routine queries.

### 6. Be Honest About Fragility
If your skill relies on HTML scraping, API fragility, or other brittle patterns, say so. Don't hide implementation details that affect result quality. The HTML Parsing Note does this well for PaperBLAST.

Include:
- What could break (e.g., "page structure changes")
- How users can verify (e.g., "check the search_url")
- Fallback options (e.g., "visit the site directly")

This builds trust and reduces user frustration when results look odd.

### 7. Iterate Based on Real Usage
This skill was written by people who've used PaperBLAST extensively. Patterns 1-4 are based on actual workflows, not hypothetical ones. As you build skills:
- Collect examples of how users invoke your tool
- Notice patterns in queries that fail or get poor results
- Update query tips and workflow patterns based on what you learn
- Version your skill (add a `version:` field) so users know when it's been improved

---

## Summary: A Functional Model

The PaperBLAST skill is functional and learnable. It demonstrates how to wrap legacy scientific tools into Claude's ecosystem with proper structure and transparency:

- **Strengths:** Clear trigger conditions, explicit workflow patterns (including two-step GapMind flow), concrete query tips, structured JSON returns, honest about fragility
- **Weaknesses:** Minimal error handling guidance, description voice inconsistency
- **Learnings:** Frontmatter and tool reference tables matter more than prose; explicit patterns beat generic explanations; structured return types enable programmatic queries; transparency about limitations builds trust

Use this skill as a template for your own work. When you build your own metabolic pathway tools or integrate external databases, follow the same structure: clear metadata, explicit decision tables with return types, workflow patterns, and domain-specific tips. Be honest about limitations. Iterate based on usage. Your future collaborators will thank you.
