# Hackathon Project Setup Log

Date: February 2026
Org: ArkinLaboratory (https://github.com/ArkinLaboratory)
Repo: ai-skills-workshop
Project: Lab Hackathon (https://github.com/orgs/ArkinLaboratory/projects/2)

## What Was Created

### Labels (12 total, in ai-skills-workshop repo)

Track labels:
- track:skills+mcp (color #0052CC) — Skills and MCP server development
- track:lakehouse (color #006B75) — Lakehouse / BERDL data integration
- track:microbiome-foundations (color #0E8A16) — Microbiome foundations and analysis

Difficulty labels:
- starter (color #C2E0C6) — Good first task, minimal setup
- intermediate (color #FEF2C0) — Some coding or domain knowledge
- advanced (color #F9D0C4) — Significant implementation effort

Sub-area labels:
- paperblast (#D4C5F9) — PaperBLAST / Curated BLAST / GapMind
- gapmind (#C5DEF5) — GapMind metabolic analysis
- hello-world (#E4E669) — Hello World skill/MCP examples
- berdl (#BFD4F2) — BERDL / ENIGMA data tools

Type labels:
- documentation (#0075CA) — Documentation improvements
- hackathon (#D93F0B) — Hackathon task

### Seed Issues (11, all labeled `hackathon`)

| # | Title | Track | Difficulty |
|---|-------|-------|------------|
| 1 | Try the Hello World skill (5 min) | Skills+MCP | Starter |
| 2 | Install and test the PaperBLAST skill | Skills+MCP | Starter |
| 3 | Build a skill for your favorite bioinformatics tool | Skills+MCP | Intermediate |
| 4 | Write an MCP server for a new papers.genomics.lbl.gov endpoint | Skills+MCP | Advanced |
| 5 | Add error handling and retry logic to PaperBLAST MCP | Skills+MCP | Intermediate |
| 6 | Create a skill for querying KBase data | Skills+MCP | Intermediate |
| 7 | Review and improve the Skill Authoring Guide | Skills+MCP | Starter |
| 8 | Explore the BERDL-ENIGMA-CORAL DuckDB MCP | Lakehouse | Starter |
| 9 | Build a lakehouse MCP for a new BERDL dataset | Lakehouse | Advanced |
| 10 | Create a skill for common microbiome analysis workflows | MicrobiomeFoundations | Intermediate |
| 11 | Build an MCP for querying GTDB taxonomy | MicrobiomeFoundations | Advanced |

### GitHub Project

- Name: Lab Hackathon
- Level: Organization (ArkinLaboratory)
- URL: https://github.com/orgs/ArkinLaboratory/projects/2
- All 11 issues added to the project

## Setup Script

Location: `setup/create-hackathon-project.sh`

The script handles labels, issues, project creation, and adding issues to the project in one run. It's idempotent for labels (`--force` flag) but will create duplicate issues if re-run.

### Prerequisites

- `gh` CLI installed and authenticated (`gh auth login`)
- `project` scope added to auth token (`gh auth refresh -s project`)

### Running

```bash
gh auth login
gh auth refresh -s project
bash setup/create-hackathon-project.sh
```

## Gotchas Encountered

### 1. `gh project create --format board` — invalid flag

**Problem:** The script originally used `--format board` on `gh project create`. The `--format` flag on this command only accepts `json` (it controls output serialization, not project layout). The error:

```
invalid argument "board" for "--format" flag: valid values are {json}
```

**Fix:** Removed `--format board`. Projects v2 are created as a default table view. Board, roadmap, and other views are added in the web UI after creation.

### 2. Missing `project` auth scope

**Problem:** The default `gh auth login` flow does NOT include the `project` scope. Labels and issues create fine, but `gh project create` fails with:

```
error: your authentication token is missing required scopes [project]
```

**Fix:** Run `gh auth refresh -s project` to add the scope. The script now checks for this and warns before proceeding.

### 3. Labels and issues are idempotent; projects and issue-adds are not

Labels use `--force`, so re-running creates or updates. But `gh issue create` will create duplicate issues on re-run, and `gh project item-add` will silently succeed if the item is already there. If you need to re-run after a partial failure, either skip the already-completed sections or manually clean up duplicates.

## Manual Steps Required (Web UI)

These cannot be done via `gh` CLI — they require the GitHub web interface:

1. **Add custom fields** (in the project at https://github.com/orgs/ArkinLaboratory/projects/2):
   - Click `+` on the table header → "New field"
   - Create **Track** (Single select): `Skills+MCP`, `Lakehouse`, `MicrobiomeFoundations`
   - Create **Difficulty** (Single select): `Starter`, `Intermediate`, `Advanced`
   - Set field values for each issue

2. **Create views:**
   - Click "New view" → choose Board layout for board view
   - Optionally create filtered views per track

3. **Enable workflows** (optional):
   - In the project, click ⋯ (three-dot menu) → look for Workflows
   - Enable "Item closed" → set Status to "Done"
   - Enable "Pull request merged" → set Status to "Done"
   - (Note: this UI location varies by GitHub version; may be under ⋯ → Settings → Workflows)

## Adding New Content Later

### New tracks
Edit the "Track" custom field in the Project settings — add a new dropdown option. Optionally create a matching label:
```bash
gh label create "track:new-track" --repo ArkinLaboratory/ai-skills-workshop --color "1D76DB" --force
```

### New issues
```bash
gh issue create --repo ArkinLaboratory/ai-skills-workshop \
  --title "Your issue title" \
  --body "Description..." \
  --label "hackathon,track:skills+mcp,intermediate"

# Then add to the project (project number 2):
gh project item-add 2 --owner ArkinLaboratory --url <ISSUE_URL>
```

### New labels
```bash
gh label create "label-name" --repo ArkinLaboratory/ai-skills-workshop --color "HEXCOLOR" --description "Description" --force
```
