#!/usr/bin/env bash
#
# create-hackathon-project.sh
#
# Sets up the GitHub Project, labels, and seed issues for the Arkin Lab Hackathon.
# Run this once from your local machine (requires `gh` CLI, authenticated).
#
# Usage:
#   gh auth login                          # if not already authenticated
#   gh auth refresh -s project             # add the "project" scope (required for gh project commands)
#   bash setup/create-hackathon-project.sh
#
# What it does:
#   1. Creates labels in the ai-skills-workshop repo (tracks, difficulty, sub-areas)
#   2. Creates seed issues in ai-skills-workshop
#   3. Creates an org-level GitHub Project "Lab Hackathon"
#   4. Adds all issues to the Project
#
# You'll finish setup in the GitHub web UI:
#   - Add custom fields (Track, Difficulty) to the Project
#   - Create filtered views per track
#   - Drag issues into Status columns
#
set -euo pipefail

ORG="ArkinLaboratory"
REPO="ai-skills-workshop"
FULL_REPO="$ORG/$REPO"

echo "=== Arkin Lab Hackathon — GitHub Project Setup ==="
echo ""

# ── 0. Preflight ──────────────────────────────────────────────────────────────

if ! command -v gh &>/dev/null; then
  echo "ERROR: gh CLI not found. Install: https://cli.github.com"
  exit 1
fi

if ! gh auth status &>/dev/null; then
  echo "ERROR: Not authenticated. Run: gh auth login"
  exit 1
fi

# The "project" scope is required for gh project create/item-add but is NOT
# included in the default gh auth login flow. Check for it explicitly.
if ! gh auth status 2>&1 | grep -q "project"; then
  echo "WARNING: Your auth token may be missing the 'project' scope."
  echo "  Run:  gh auth refresh -s project"
  echo "  Then re-run this script."
  echo ""
  echo "  (Labels and issues will still work, but project creation will fail.)"
  read -rp "Continue anyway? [y/N] " answer
  [[ "$answer" =~ ^[Yy] ]] || exit 1
fi

echo "Authenticated as: $(gh auth status 2>&1 | grep 'Logged in' | head -1)"
echo "Org: $ORG"
echo "Repo: $FULL_REPO"
echo ""

# ── 1. Create Labels ─────────────────────────────────────────────────────────
#
# gh label create is idempotent — safe to re-run.
# Colors: track=blue shades, difficulty=green shades, sub-area=purple shades

echo "── Creating labels ──"

# Track labels (shown on Project board as grouping)
gh label create "track:skills+mcp"              --repo "$FULL_REPO" --color "0052CC" --description "Skills and MCP server development"            --force
gh label create "track:lakehouse"               --repo "$FULL_REPO" --color "006B75" --description "Lakehouse / BERDL data integration"            --force
gh label create "track:microbiome-foundations"   --repo "$FULL_REPO" --color "0E8A16" --description "Microbiome foundations and analysis"            --force

# Difficulty labels
gh label create "starter"      --repo "$FULL_REPO" --color "C2E0C6" --description "Good first task, minimal setup"     --force
gh label create "intermediate" --repo "$FULL_REPO" --color "FEF2C0" --description "Some coding or domain knowledge"    --force
gh label create "advanced"     --repo "$FULL_REPO" --color "F9D0C4" --description "Significant implementation effort"   --force

# Sub-area labels (for filtering within a track)
gh label create "paperblast"    --repo "$FULL_REPO" --color "D4C5F9" --description "PaperBLAST / Curated BLAST / GapMind" --force
gh label create "gapmind"       --repo "$FULL_REPO" --color "C5DEF5" --description "GapMind metabolic analysis"            --force
gh label create "hello-world"   --repo "$FULL_REPO" --color "E4E669" --description "Hello World skill/MCP examples"        --force
gh label create "berdl"         --repo "$FULL_REPO" --color "BFD4F2" --description "BERDL / ENIGMA data tools"             --force

# Type labels
gh label create "documentation" --repo "$FULL_REPO" --color "0075CA" --description "Documentation improvements"    --force
gh label create "hackathon"     --repo "$FULL_REPO" --color "D93F0B" --description "Hackathon task"                --force

echo "Labels created."
echo ""

# ── 2. Create Seed Issues ────────────────────────────────────────────────────
#
# Each issue gets: title, body, labels.
# We collect the issue URLs so we can add them to the Project later.

echo "── Creating seed issues ──"

ISSUE_URLS=()

create_issue() {
  local title="$1"
  local body="$2"
  local labels="$3"
  local url
  url=$(gh issue create --repo "$FULL_REPO" \
    --title "$title" \
    --body "$body" \
    --label "$labels" 2>&1)
  echo "  Created: $title"
  ISSUE_URLS+=("$url")
}

# ── Skills+MCP Track: Starter ────────────────────────────────────────────────

create_issue \
  "Try the Hello World skill (5 min)" \
  "$(cat <<'EOF'
**Track:** Skills+MCP · **Difficulty:** Starter · **Time:** 5 minutes

### Goal
Install and test the simplest possible skill to verify your Claude setup works.

### Steps
1. Follow [examples/skills/01-hello-world/README.md](../examples/skills/01-hello-world/README.md)
2. Copy the SKILL.md to `~/.claude/skills/haiku-bio/`
3. Start a new Claude conversation and ask a biology question
4. Verify Claude responds with a haiku

### Success Criteria
Claude generates biology-themed haikus when prompted.

### What You Learn
- How skills are installed (`~/.claude/skills/`)
- How Claude discovers and loads skills automatically
- The minimal structure of a SKILL.md file
EOF
)" \
  "hackathon,track:skills+mcp,hello-world,starter"

create_issue \
  "Install and test the PaperBLAST skill" \
  "$(cat <<'EOF'
**Track:** Skills+MCP · **Difficulty:** Starter · **Time:** 20-30 minutes

### Prerequisites
- LBNL VPN connected (see INSTALL.md for setup)
- Python 3.10+

### Goal
Get the full PaperBLAST skill working: 5 MCP tools for protein literature search,
curated enzyme lookup, and metabolic pathway analysis.

### Steps
1. Follow [examples/skills/02-paperblast/INSTALL.md](../examples/skills/02-paperblast/INSTALL.md)
2. Run `check_deps.py --live` to verify connectivity
3. Copy skill + register MCP
4. Test with: "Search PaperBLAST for MinD (P0AEZ3)"
5. Try all 5 tools (see USAGE-EXAMPLES.md)

### Success Criteria
All 5 tools return structured results: `paperblast_search`, `paperblast_gene_papers`,
`curated_blast_search`, `gapmind_check`, `gapmind_list_organisms`.

### What You Learn
- Skill + MCP pairing pattern
- How structured JSON output works with Pydantic models
- The two-step GapMind workflow
EOF
)" \
  "hackathon,track:skills+mcp,paperblast,starter"

# ── Skills+MCP Track: Intermediate ───────────────────────────────────────────

create_issue \
  "Build a skill for your favorite bioinformatics tool" \
  "$(cat <<'EOF'
**Track:** Skills+MCP · **Difficulty:** Intermediate · **Time:** 1-2 hours

### Goal
Create a new skill that teaches Claude about a bioinformatics tool or database
you use regularly.

### Steps
1. Pick a tool (BLAST, UniProt, KEGG, InterPro, your lab's pipeline, etc.)
2. Use `templates/skill-template/SKILL.md` as a starting point
3. Follow the [Skill Authoring Guide](docs/skill-authoring-guide.md)
4. Write trigger conditions, workflow patterns, and query tips
5. Install and test it
6. Submit a PR

### Guidance
- Read [docs/paperblast-skill-design.md](docs/paperblast-skill-design.md) for a
  worked example of how to structure a real skill
- Focus on the description field (triggers) and tool reference table first
- Start with a skill-only approach (no MCP) if the tool has a web interface Claude
  can reason about

### Success Criteria
- SKILL.md follows the authoring guide structure
- Claude correctly identifies when to activate the skill
- At least 2 workflow patterns documented
EOF
)" \
  "hackathon,track:skills+mcp,intermediate"

create_issue \
  "Write an MCP server for a new papers.genomics.lbl.gov endpoint" \
  "$(cat <<'EOF'
**Track:** Skills+MCP · **Difficulty:** Advanced · **Time:** 2-4 hours

### Goal
Extend the PaperBLAST ecosystem by wrapping another Morgan Price tool as an MCP server.

### Available Endpoints (see references/setup.md)
- **Fitness Browser** — gene fitness data across conditions
- **fast.genomics** — fast genome comparisons
- **SitesBLAST** — conserved active site search
- **Sites on a Tree** — phylogenetic site analysis
- **HMM Search** — protein family search

### Steps
1. Pick an endpoint from the list above
2. Study the PaperBLAST MCP as a model (`scripts/paperblast_mcp.py`)
3. Use `templates/mcp-template/server.py` as a starting point
4. Write HTML parsing logic for the CGI output
5. Define Pydantic output models (follow `scripts/models.py` pattern)
6. Register with `claude mcp add` and test
7. Submit a PR

### Success Criteria
- MCP server starts and connects
- At least one tool returns structured data
- HTML parsing handles common edge cases
- SKILL.md updated to include the new tool
EOF
)" \
  "hackathon,track:skills+mcp,paperblast,advanced"

create_issue \
  "Add error handling and retry logic to PaperBLAST MCP" \
  "$(cat <<'EOF'
**Track:** Skills+MCP · **Difficulty:** Intermediate · **Time:** 1-2 hours

### Problem
The PaperBLAST MCP server has no retry logic. If papers.genomics.lbl.gov is slow
or returns a transient error, the tool fails immediately.

### Goal
Add configurable retry logic with exponential backoff, and improve error messages
so Claude can communicate failures clearly to the user.

### Scope
- Add retry with backoff to all HTTP requests in `paperblast_mcp.py`
- Return structured error responses (not raw exceptions)
- Add timeout configuration
- Update SKILL.md workflow patterns with error-handling guidance

### Success Criteria
- Transient 5xx errors retry automatically (up to 3 attempts)
- Timeout errors return a clear message with the URL for manual verification
- Claude can distinguish between "server down" and "no results found"
EOF
)" \
  "hackathon,track:skills+mcp,paperblast,intermediate"

create_issue \
  "Create a skill for querying KBase data" \
  "$(cat <<'EOF'
**Track:** Skills+MCP · **Difficulty:** Intermediate · **Time:** 2-3 hours

### Goal
Write a skill (and optionally an MCP server) that helps Claude interact with KBase
narratives, genomes, or metabolic models.

### Possible Approaches
- **Skill-only:** Teach Claude about KBase APIs, narrative structure, and how to
  guide users through KBase workflows
- **Skill + MCP:** Wrap the KBase API to let Claude query genomes, fetch narratives,
  or run simple analyses

### Resources
- KBase API docs: https://kbase.us/services/
- KBase SDK: https://github.com/kbase/kb_sdk
- Existing lakehouse-skills: https://github.com/cmungall/lakehouse-skills

### Success Criteria
- Skill correctly triggers on KBase-related queries
- At least one useful workflow pattern documented
- Tested against real KBase data
EOF
)" \
  "hackathon,track:skills+mcp,intermediate"

# ── Skills+MCP Track: Documentation ──────────────────────────────────────────

create_issue \
  "Review and improve the Skill Authoring Guide" \
  "$(cat <<'EOF'
**Track:** Skills+MCP · **Difficulty:** Starter · **Time:** 30-60 minutes

### Goal
Read through `docs/skill-authoring-guide.md` with fresh eyes and suggest improvements.

### Steps
1. Read the guide end-to-end
2. Try following it to build a simple skill
3. Note where you got confused, where steps were missing, or where
   examples didn't match reality
4. Submit a PR with fixes, or create issues for problems you find

### Success Criteria
- At least 3 concrete improvements identified
- PR submitted with fixes or detailed issue descriptions
EOF
)" \
  "hackathon,track:skills+mcp,documentation,starter"

# ── Lakehouse Track ──────────────────────────────────────────────────────────

create_issue \
  "Explore the BERDL-ENIGMA-CORAL DuckDB MCP" \
  "$(cat <<'EOF'
**Track:** Lakehouse · **Difficulty:** Starter · **Time:** 30-60 minutes

### Goal
Install and test the existing BERDL-ENIGMA-CORAL MCP server, which provides
natural-language access to ENIGMA isolate and environmental data via DuckDB.

### Steps
1. Clone https://github.com/jmchandonia/BERDL-ENIGMA-CORAL
2. Follow the setup instructions
3. Register as an MCP with `claude mcp add`
4. Try queries like "What ENIGMA isolates were collected from groundwater?"
5. Document what works and what doesn't

### Success Criteria
- MCP connects and responds to queries
- At least 5 test queries documented with results
- Known limitations or bugs filed as issues
EOF
)" \
  "hackathon,track:lakehouse,berdl,starter"

create_issue \
  "Build a lakehouse MCP for a new BERDL dataset" \
  "$(cat <<'EOF'
**Track:** Lakehouse · **Difficulty:** Advanced · **Time:** 3-4 hours

### Goal
Create an MCP server that exposes a new BERDL dataset (not already covered by
BERDL-ENIGMA-CORAL) via natural-language queries.

### Possible Datasets
- Fitness data (gene fitness across conditions)
- Metagenome assemblies
- Metabolomics measurements
- Environmental sensor data

### Steps
1. Identify a dataset in the BERDL lakehouse
2. Set up a DuckDB (or SQLite) interface to the data
3. Build an MCP server with tools for common queries
4. Write a companion SKILL.md with domain guidance
5. Test and submit a PR

### Success Criteria
- MCP server connects and returns structured data
- At least 3 tools covering common query patterns
- SKILL.md with workflow patterns and query tips
EOF
)" \
  "hackathon,track:lakehouse,berdl,advanced"

# ── MicrobiomeFoundations Track ──────────────────────────────────────────────

create_issue \
  "Create a skill for common microbiome analysis workflows" \
  "$(cat <<'EOF'
**Track:** MicrobiomeFoundations · **Difficulty:** Intermediate · **Time:** 2-3 hours

### Goal
Write a skill that teaches Claude about standard microbiome analysis pipelines:
16S/ITS amplicon analysis, metagenome assembly, MAG binning, taxonomic profiling.

### Scope
- Skill-only (no MCP needed): teach Claude the decision logic for when to use
  which tools (QIIME2 vs mothur vs DADA2, MetaSPAdes vs MEGAHIT, etc.)
- Include workflow patterns for common lab scenarios
- Query tips for interpreting diversity metrics, quality thresholds, etc.

### Success Criteria
- SKILL.md follows the authoring guide structure
- Covers at least 3 distinct workflow patterns
- Includes concrete "good input / bad input" examples
- Tested with realistic prompts
EOF
)" \
  "hackathon,track:microbiome-foundations,intermediate"

create_issue \
  "Build an MCP for querying GTDB taxonomy" \
  "$(cat <<'EOF'
**Track:** MicrobiomeFoundations · **Difficulty:** Advanced · **Time:** 3-4 hours

### Goal
Create an MCP server that lets Claude query GTDB (Genome Taxonomy Database)
for taxonomic classification, lineage lookups, and genome metadata.

### Resources
- GTDB API: https://gtdb.ecogenomic.org/api
- GTDB-Tk: https://github.com/Ecogenomics/GTDBTk

### Steps
1. Explore the GTDB API endpoints
2. Build an MCP server with tools for:
   - Taxonomy lookup by genome accession
   - Lineage traversal (species → genus → family → ...)
   - Search by taxonomic name
3. Write Pydantic output models
4. Write a companion SKILL.md
5. Test and submit a PR

### Success Criteria
- At least 3 tools returning structured JSON
- SKILL.md with workflow patterns for taxonomy queries
- Handles edge cases (unknown genomes, ambiguous names)
EOF
)" \
  "hackathon,track:microbiome-foundations,advanced"

echo ""
echo "Created ${#ISSUE_URLS[@]} issues."
echo ""

# ── 3. Create the GitHub Project ─────────────────────────────────────────────

echo "── Creating GitHub Project ──"

PROJECT_URL=$(gh project create \
  --owner "$ORG" \
  --title "Lab Hackathon" 2>&1)

echo "Project created: $PROJECT_URL"
echo ""

# Extract project number from URL (e.g., https://github.com/orgs/ArkinLaboratory/projects/1)
PROJECT_NUM=$(echo "$PROJECT_URL" | grep -oE '[0-9]+$')

if [ -z "$PROJECT_NUM" ]; then
  echo "WARNING: Could not extract project number from: $PROJECT_URL"
  echo "You may need to add issues to the project manually."
  echo "List projects with: gh project list --owner $ORG"
  echo ""
else
  # ── 4. Add Issues to the Project ─────────────────────────────────────────────

  echo "── Adding issues to project #$PROJECT_NUM ──"

  for url in "${ISSUE_URLS[@]}"; do
    gh project item-add "$PROJECT_NUM" --owner "$ORG" --url "$url" 2>/dev/null && \
      echo "  Added: $url" || \
      echo "  WARN: Failed to add: $url"
  done

  echo ""
fi

# ── 5. Summary ───────────────────────────────────────────────────────────────

cat <<'SUMMARY'
=== Setup Complete ===

Next steps (in the GitHub web UI):

1. Go to: https://github.com/orgs/ArkinLaboratory/projects
   Open the "Lab Hackathon" project.

2. Add custom fields:
   - Click "+" on the table header → "New field"
   - Create "Track" (Single select): Skills+MCP, Lakehouse, MicrobiomeFoundations
   - Create "Difficulty" (Single select): Starter, Intermediate, Advanced
   - Set field values for each issue (or use the table/board view)

3. Create views:
   - "Overview Board": Board layout, group by Status
   - "Skills+MCP": Board layout, filter by Track=Skills+MCP
   - "Lakehouse": Board layout, filter by Track=Lakehouse
   - "MicrobiomeFoundations": Board layout, filter by Track=MicrobiomeFoundations
   - "By Assignee": Table layout, group by Assignee

4. Set up automation (optional):
   - Settings → Workflows → "Item closed" → Set Status to "Done"
   - Settings → Workflows → "Pull request merged" → Set Status to "Done"

To add more tracks later:
   - Edit the "Track" field in Project settings → add a new option
   - Create a new label: gh label create "track:new-track" --repo ArkinLaboratory/ai-skills-workshop --color "1D76DB" --force

To add more issues:
   gh issue create --repo ArkinLaboratory/ai-skills-workshop --title "..." --body "..." --label "hackathon,track:skills+mcp,intermediate"
   gh project item-add <PROJECT_NUM> --owner ArkinLaboratory --url <ISSUE_URL>

SUMMARY
