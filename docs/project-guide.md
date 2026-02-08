# Using the Hackathon Project Board

## Where Things Live

- **Project board:** https://github.com/orgs/ArkinLaboratory/projects/2
  The project board shows all hackathon tasks organized by status. Switch between Table view and Board view using the tabs at the top.

- **Issues:** https://github.com/ArkinLaboratory/ai-skills-workshop/issues
  Each task is a GitHub issue. The issue contains the full description, steps, and success criteria.

- **Repository:** https://github.com/ArkinLaboratory/ai-skills-workshop
  The actual code and documentation.

## Understanding the Board

### Status columns (on the Board view)
- **No Status / Todo** — Available work. Pick something here.
- **In Progress** — Someone is actively working on it.
- **Done** — Completed and merged.

### Labels
Each issue has labels that tell you:
- **Track**: `track:skills+mcp`, `track:lakehouse`, or `track:microbiome-foundations` — which area of the hackathon
- **Difficulty**: `starter` (good first task), `intermediate` (some coding/domain knowledge), `advanced` (significant effort)
- **Sub-area**: `paperblast`, `gapmind`, `hello-world`, `berdl` — specific tools or datasets involved

### Custom fields (visible in Table view)
- **Track** — same as the track label, but as a sortable/filterable field
- **Difficulty** — same as difficulty label, as a sortable field

## How to Work on an Issue

### 1. Find an issue
Browse the project board or the issues list. Filter by label if you want a specific track or difficulty:
- Click "Filter" on the board and select labels
- Or in the issues list: https://github.com/ArkinLaboratory/ai-skills-workshop/issues?q=label%3Astarter

### 2. Claim it
- Open the issue
- Assign yourself (click "Assignees" in the right sidebar → select your name)
- Leave a comment like "I'm working on this" so others know
- On the project board, drag the issue to "In Progress" (or change the Status field)

### 3. Create a branch
```bash
cd ai-skills-workshop
git checkout main
git pull
git checkout -b issue-7-improve-authoring-guide   # use the issue number in the branch name
```

### 4. Do the work
Follow the steps in the issue description. The issue body tells you what to build, where to start, and what success looks like.

### 5. Commit and push
```bash
git add .
git commit -m "Improve skill authoring guide examples. Fixes #7"
git push -u origin issue-7-improve-authoring-guide
```

Using `Fixes #7` (or `Closes #7` or `Resolves #7`) in the commit message will automatically close the issue when the PR is merged.

### 6. Open a pull request
```bash
gh pr create --title "Improve skill authoring guide examples" --body "Fixes #7

Added clearer examples for trigger conditions and workflow patterns."
```

### 7. Update the board
Once your PR is merged:
- The issue closes automatically (if you used `Fixes #N`)
- Drag the issue to "Done" on the project board (or it may move automatically if workflows are enabled)
- Delete your local branch: `git checkout main && git pull && git branch -d issue-7-improve-authoring-guide`

## Creating New Issues

Found a bug? Have an idea for a new task? Create an issue:

```bash
gh issue create --repo ArkinLaboratory/ai-skills-workshop \
  --title "Bug: check_deps.py fails on Apple Silicon" \
  --body "The lxml installation fails on M1/M2 Macs..." \
  --label "hackathon,track:skills+mcp,starter"
```

Or use the GitHub web UI: go to the Issues tab → New Issue.

To add it to the project board:
```bash
gh project item-add 2 --owner ArkinLaboratory --url <paste-the-issue-url>
```

(You need the `project` auth scope for this: `gh auth refresh -s project`)

## Tips

- **Start with a `starter` issue** if you're new to GitHub or to the workshop tools. The Hello World skill (#1) takes 5 minutes.
- **Check the issue comments** before claiming — someone may already be working on it.
- **Ask in the hackathon Slack channel** if you're stuck. Paste the issue URL so people can see what you're working on.
- **One person per issue** unless it's explicitly marked for pair/group work.
- **Don't sit on issues** — if you claim something but can't finish, unassign yourself so someone else can pick it up.
- **PaperBLAST issues require LBNL VPN** — see [INSTALL.md](../examples/skills/02-paperblast/INSTALL.md) for VPN setup.

## Quick Reference

| Action | Command |
|--------|---------|
| Browse issues | `gh issue list --repo ArkinLaboratory/ai-skills-workshop --label hackathon` |
| Filter by difficulty | `gh issue list --repo ArkinLaboratory/ai-skills-workshop --label starter` |
| Filter by track | `gh issue list --repo ArkinLaboratory/ai-skills-workshop --label "track:skills+mcp"` |
| View an issue | `gh issue view 7 --repo ArkinLaboratory/ai-skills-workshop` |
| Assign yourself | `gh issue edit 7 --repo ArkinLaboratory/ai-skills-workshop --add-assignee @me` |
| Create a PR for an issue | `gh pr create --title "Fix X" --body "Fixes #7"` |
| Add issue to project | `gh project item-add 2 --owner ArkinLaboratory --url <URL>` |
| List project items | `gh project item-list 2 --owner ArkinLaboratory` |
