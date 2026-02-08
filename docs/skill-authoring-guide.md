# Skill Authoring Guide

This guide teaches you how to write high-quality Claude skills for the AI Skills Workshop. You understand what a skill is; this document covers *how to write one that actually works*.

Skills are directories containing structured instructions that teach Claude when and how to use specific tools. A good skill helps Claude make intelligent decisions about *what to do*, not just *how to do it*. This guide emphasizes practical patterns that work across bioinformatics workflows. For a worked example applying these principles to a real skill, see the [PaperBLAST Skill Design Case Study](paperblast-skill-design.md).

## Skill Directory Structure

Every skill lives in a directory with a required `SKILL.md` file and optional subdirectories for code and documentation:

```
my-skill/
├── SKILL.md              # Required: frontmatter + instructions
├── scripts/              # Optional: executable code (Python, Bash, etc.)
├── references/           # Optional: supplementary docs (loaded on demand)
└── assets/               # Optional: templates, images, config files
```

The minimal skill is just `SKILL.md`. Add subdirectories only when you have bundles code or detailed reference materials that aren't needed immediately.

## Skill Scope and Distribution

Skills can exist at three scope levels, each serving different purposes:

**User scope** (`~/.claude/skills/`) stores skills available across all your projects. These are personal utilities—think of them as tools in your personal toolkit. Use user-scope skills for things you build for yourself and want available everywhere.

**Project scope** (`.claude/skills/` in a repo) stores skills that ship with a project. This is the version-controlled approach. Skills here are shared via git, so teammates automatically get them when they clone the repository. For the workshop, this is your default choice. If you're building a skill for the team to use, put it in `.claude/skills/` and commit it.

**Plugin-provided skills** come from Claude's marketplaces and are installed separately.

The decision is straightforward: if the skill is personal, use `~/.claude/skills/`. If it supports the team's work on this project, use `.claude/skills/` in the repo and commit it to version control.

## SKILL.md Format: Frontmatter and Body

Every skill file has two sections: YAML frontmatter (metadata) and a markdown body (instructions).

```yaml
---
name: searching-paperblast
description: >
  Search PaperBLAST for papers about proteins and genes, find characterized
  proteins by function, and check metabolic pathway gaps with GapMind. Use when
  user asks about literature for a protein, wants to find proteins by function,
  or asks about organism biosynthetic capability.
version: "1.0.0"
---

# Usage

Research the protein specified in your request...
```

The frontmatter tells Claude *whether to load the skill*. The body tells Claude *what to do* once loaded. This separation matters: Claude scans frontmatter from all skills at startup to decide availability, but only reads the body when you explicitly invoke the skill or when Claude determines the skill is relevant.

### Required Frontmatter Fields

**`name`** (string, 64 characters max, lowercase letters/numbers/hyphens only) becomes your skill's slash command. Use gerund form: `analyzing-sequences`, `searching-papers`, `validating-genomes`. The name should be memorable and self-documenting. Avoid reserved words and XML tags.

**`description`** (string, 1024 characters max) is the most important field. This is what Claude reads at startup to decide whether the skill is relevant to the user's request. Write it in third person. Be comprehensive: list *all* the trigger conditions that should activate this skill. Include specific terms users might say when they want this skill. This field is not "when to use"—it's the decision logic Claude uses to determine relevance.

A good description is like a function signature: it tells you exactly what this skill does and when it applies.

Example of a well-written description:

```yaml
description: >
  Search PaperBLAST for literature about proteins and genes, find characterized
  proteins matching a functional description via Curated BLAST, and check
  metabolic pathway gaps with GapMind. Triggers on: (1) user asks about papers
  or literature for a specific protein or gene, (2) user wants to find proteins
  with a particular function, (3) user asks about amino acid biosynthesis or
  carbon source utilization in an organism, (4) user mentions PaperBLAST,
  GapMind, or Curated BLAST by name, (5) user wants to annotate hypothetical
  proteins using literature evidence.
```

Compare this to a weak description:

```yaml
description: A skill for working with PaperBLAST.
```

The weak version tells you what the skill is, not when to use it. Claude won't know whether to activate it in response to "find papers about HoxB" or "what's the best way to search literature?"

### Optional Behavioral Fields

**`disable-model-invocation`** (boolean) prevents Claude from automatically invoking the skill. When `true`, only the user can call it via `/skill-name`. Use this for skills with side effects—deploy commands, sending messages, committing code, or any action you want human approval for. With this flag set, Claude can still read the skill's documentation but won't decide to use it on its own.

**`user-invocable`** (boolean) does the opposite: when `false`, only Claude can invoke the skill. The user cannot call it manually via slash command. Use this for background knowledge or internal utilities that aren't meant as direct commands. Example: a skill that teaches Claude about your lab's naming conventions might set `user-invocable: false` so Claude loads it automatically but the user doesn't need to know it exists.

**`allowed-tools`** (string) restricts which Claude tools this skill can use. This is a security boundary when skills include bundled scripts that might be powerful. Example: `allowed-tools: Read, Grep, Bash(git *)` allows the skill to read files, search with grep, and run git commands but nothing else. Without this restriction, a skill's bundled scripts could theoretically use any tool Claude has access to.

**`context`** (string) controls execution environment. `context: fork` runs the skill in a subagent with its own context. Use this for long-running or context-heavy tasks that you don't want to consume your main token budget. The subagent has its own context window and doesn't interfere with your conversation.

**`agent`** (string) specifies a specialized agent. Example: `agent: Explore` for skills that need to explore a large codebase. This routes the skill to an agent optimized for that kind of work.

**`version`** (string) is metadata for tracking. Example: `version: "1.0.0"`. Useful if you're managing multiple versions of a skill.

**`mode`** (boolean) categorizes the skill as a "mode command" that modifies Claude's behavior for the session. These appear in a special section of the skill list and are used for things like "enable debug mode" or "use verbose output".

### Body Content

The markdown body is the actual skill instructions. This is what Claude reads when it decides to use your skill. Write it as you would any Claude prompt: be clear, be specific, use examples. The body is where you explain:

- What specific tasks the skill accomplishes
- What Claude should do step-by-step
- What tools are available and when to use them
- Workflow patterns that work well
- Examples of expected outputs

Keep the body under 500 lines. Detailed reference material belongs in `references/`, not here.

## Progressive Disclosure: How Skills Load

This is the key insight for writing efficient skills. Skills load in three stages:

**Stage 1: Metadata scan** (~100 tokens at startup). Claude reads `name` and `description` from every installed skill. This happens once per session. This is where Claude decides "okay, the user might want to use the PaperBLAST skill for this request."

**Stage 2: Full SKILL.md** (<5000 tokens, ideally <2000). When Claude decides to use your skill, it loads the entire `SKILL.md` body. This should contain your core instructions, tool references, and workflow patterns.

**Stage 3: Bundled resources** (on demand). Claude loads files from `scripts/`, `references/`, and `assets/` only when needed, via the `Read` tool. Scripts execute and only their *output* consumes tokens. Reference documents are loaded on demand. Assets are never loaded into context.

The implication for writing good skills:

1. **Put trigger logic in the description.** If it's not in the description, Claude won't know when to use the skill.
2. **Put core instructions in the body.** This is what Claude reads when actively using the skill.
3. **Put detailed material in subdirectories.** Use `references/` for API docs, implementation details, or domain knowledge that's only relevant in specific scenarios.

A common mistake is front-loading all your reference material into the main `SKILL.md`. This bloats the body and wastes tokens. Instead, write a concise body that explains the workflow, then reference supporting docs: "For detailed configuration options, see `references/config.md`."

## Writing Effective Descriptions

The description is where most skills fail. A poor description means the skill never triggers, or triggers inappropriately.

Follow these rules:

**Write in third person.** "Searches PaperBLAST for proteins," not "Search PaperBLAST for proteins." The description is Claude reading about the skill, not Claude being commanded.

**Enumerate all trigger conditions.** Don't assume Claude will infer when to use your skill. Be explicit. If your skill handles "finding papers," "annotating proteins," and "checking metabolic pathways," list all three. Use "use when:" followed by numbered conditions.

**Include user vocabulary.** If users say "find papers about HoxB" and "search literature for HOX proteins," your description should include both "papers" and "literature", "find" and "search". Think about the different ways someone might ask for your skill's capability.

**Don't put "when to use" in the body.** Once Claude reads the body, the triggering decision is already made. Putting "When to Use" sections in the body wastes space. The trigger logic belongs in the description.

**Stay under 1024 characters.** This isn't a hard limit, but it's a good target. Conciseness forces you to prioritize trigger conditions.

Here's a strong description for a bioinformatics skill:

```yaml
description: >
  Analyze DNA sequences for open reading frames, coding regions, and regulatory
  elements. Transcribe DNA to RNA, translate to protein. Use when: (1) user
  provides a DNA sequence and asks to find genes or ORFs, (2) user asks to
  translate DNA to protein or predict coding regions, (3) user wants to identify
  promoters, ribosome binding sites, or regulatory motifs, (4) user provides
  sequences and asks "find the gene" or "what does this code for", (5) user
  wants to design primers for a region.
```

This description tells Claude exactly when to activate this skill. It covers five distinct trigger scenarios and uses keywords users would naturally say.

## Using $ARGUMENTS for Parameterized Skills

Some skills need user input to start working. The `$ARGUMENTS` placeholder lets you capture what the user types after the slash command.

If a user types `/deep-research quantum computing`, then `$ARGUMENTS` is replaced with `quantum computing` in the skill body.

Use this pattern when your skill is a parameterized command:

```markdown
# Deep Research: $ARGUMENTS

Your task is to conduct thorough research on the following topic: $ARGUMENTS

1. Search for recent papers and articles
2. Identify key concepts and definitions
3. Find practical applications
4. Summarize findings with citations
```

When the user invokes `/deep-research protein folding`, that becomes:

```markdown
Your task is to conduct thorough research on the following topic: protein folding
```

This is useful for general-purpose research skills, prompt expansion skills, or anything where the user provides the subject matter.

## Bundled Resources: Scripts, References, and Assets

### Scripts Subdirectory

The `scripts/` directory contains executable code: Python files, Bash scripts, standalone tools. When Claude uses a script, it executes via the Bash tool—only the script's *output* consumes tokens, not the script itself.

This is powerful for data processing. Suppose you have a bioinformatics workflow:

```
sequence-analyzer/
├── SKILL.md
└── scripts/
    ├── find_orfs.py
    └── translate.py
```

Your SKILL.md tells Claude when and how to use these scripts. Claude invokes them like:

```bash
python scripts/find_orfs.py input.fasta
```

The script's output—a list of ORFs, for example—is what Claude reads and reasons about. The script itself never loads into context.

This is efficient for computationally heavy work. You can have a 500-line Python script that processes a genome, and Claude only sees the results.

Security note: if your scripts are powerful or untrusted, use `allowed-tools` in the frontmatter to restrict what the skill can do. Example: `allowed-tools: Read, Bash(python scripts/*.py)` allows only running Python scripts in the scripts directory.

### References Subdirectory

The `references/` directory stores supplementary documentation. Claude loads these files into context when needed, via the `Read` tool.

Use references for material that's detailed but not always necessary:

- API documentation for external services
- Domain knowledge that only applies in specific scenarios
- Installation instructions
- Configuration guides
- Detailed algorithm descriptions
- Large datasets or lookup tables

Example structure:

```
my-skill/
├── SKILL.md
└── references/
    ├── setup.md              # Installation instructions
    ├── api-reference.md      # Tool parameters and responses
    └── troubleshooting.md    # Common issues
```

In the main SKILL.md, reference these as needed: "For installation details, see `references/setup.md`." Claude will load the file when that reference appears in the workflow.

### Assets Subdirectory

The `assets/` directory stores files that are never loaded into context: templates, images, configuration files, fonts. These are used for output generation or as raw file resources.

If your skill generates documents, assets might contain templates:

```
report-generator/
├── SKILL.md
└── assets/
    ├── template.html
    ├── header.png
    └── style.css
```

Your SKILL.md might instruct Claude to "use the template in `assets/template.html` and save the output as report.html". Claude doesn't load the asset into context; it's used as a raw file resource.

## Pairing Skills with MCP Servers

Many real skills combine a `SKILL.md` file with an MCP (Model Context Protocol) server. The skill teaches Claude *when and how* to use tools. The MCP provides the *ability* to use those tools.

This pattern works well for integrating external services. Suppose you build a skill that searches biological databases:

```
paperblast-search/
├── SKILL.md
├── scripts/
│   └── paperblast_mcp.py      # MCP server implementing search tools
└── references/
    └── setup.md
```

The `SKILL.md` explains when to search, what search strategies work, and how to interpret results. The `paperblast_mcp.py` script exposes the actual search functions as MCP tools that Claude can invoke.

In your `SKILL.md`, include a tool reference table so Claude knows what's available:

```markdown
## Available Tools

| Tool Name | Use When | Parameters |
|-----------|----------|------------|
| `search_paperblast` | User asks about papers for a protein | `protein_name` (string), `max_results` (int) |
| `search_curated_blast` | User wants to find characterized proteins | `function` (string), `organism` (string) |
| `check_gapmind` | User asks about organism biosynthesis capability | `organism` (string), `pathway` (string) |
```

This table is critical. Without it, Claude doesn't know which tools exist or when to use them. It's part of your SKILL.md instructions.

When Claude reads this table, it understands what's available. When you combine this with a well-written description, Claude can intelligently decide to use the skill and then apply the right tool for the job.

### Registering MCP Servers for Team Distribution

MCP servers are registered to different scopes, each serving different distribution needs:

- `--scope user`: Personal scope. Stored in `~/.claude.json`. Available in all your projects. Good for personal utilities.
- `--scope project`: Project scope. Creates or updates `.mcp.json` in the project root. Shared via version control. **This is best for team workshops.** Everyone who clones the repo gets the MCP automatically.
- `--scope local` (default): Personal and project-specific. Not shared. Good for local overrides.

For team distribution, register in project scope:

```bash
# In the project root
claude mcp add --scope project paperblast python3 scripts/paperblast_mcp.py
```

This creates `.mcp.json`:

```json
{
  "mcpServers": {
    "paperblast": {
      "command": "python3",
      "args": ["scripts/paperblast_mcp.py"]
    }
  }
}
```

Commit this file to version control. When teammates clone the repository, Claude prompts them to approve the MCP server on first use (a security feature: project-scoped servers always require approval).

If your MCP needs environment variables, pass them:

```bash
claude mcp add --scope project my-server --env API_KEY=your-key python server.py
```

This stores the environment configuration in `.mcp.json` as well.

## Testing and Debugging

**Test that the skill loads:** Start a fresh Claude Code session. Ask Claude something aligned with your trigger conditions. Check Claude's reasoning (visible in the conversation) to confirm the skill was activated.

**Test with varied language:** Try 5–10 different ways to ask for what your skill does. If the skill doesn't trigger, your description likely doesn't match how users talk. Add more trigger keywords.

**Test MCP tools independently:** Before registering an MCP server, run it standalone:

```bash
python scripts/my_mcp.py
```

Make sure the server starts without errors. Check that it exposes the tools you expect. You can use the MCP Inspector to interact with the server:

```bash
npx @modelcontextprotocol/inspector python scripts/my_mcp.py
```

This opens a UI where you can test each tool and see what parameters they need.

**Test the full workflow:** Once the skill loads and the MCP is registered, ask Claude to actually use the skill end-to-end. See if Claude invokes the right tools and interprets the results correctly.

### Common Issues and Fixes

**Skill doesn't trigger.** Check your description. Does it match the words the user said? Add more trigger phrases. Examples: if your skill searches "literature," make sure the description includes "papers," "articles," "publications," etc.

**Skill triggers when it shouldn't.** Your description is too broad. Be more specific about when the skill applies. Narrow down the trigger conditions.

**MCP tool returns errors.** Test the server standalone first. Make sure Python paths and dependencies are correct. Run `python scripts/my_mcp.py` directly and look for startup errors.

**Slow responses.** Your SKILL.md is probably too long. Move detailed content to `references/`. Load it on demand, not at startup.

**Claude doesn't use the right tool.** Your tool reference table (in the skill body) might be unclear. Make sure each tool has a clear "use when" description that helps Claude decide which to invoke.

## Skill Authoring Checklist

Before deploying a skill, verify:

- [ ] `name` is lowercase, hyphenated, max 64 characters
- [ ] `description` lists all trigger conditions in third person, max 1024 characters
- [ ] Trigger conditions are in the description, not just the body
- [ ] SKILL.md body is concise, under 500 lines
- [ ] Tool reference table included (if paired with MCP)
- [ ] Workflow patterns show step-by-step usage with examples
- [ ] Detailed reference material is in `references/`, not the main body
- [ ] Scripts are tested standalone before registration
- [ ] MCP server tested with MCP Inspector (if applicable)
- [ ] Tested with at least 5 different phrasings of trigger conditions
- [ ] `assets/` directory contains only files that should never be loaded into context

A skill that passes this checklist is ready to share with the team.

## Summary

A well-authored skill teaches Claude three things: *what it does*, *when to use it*, and *how to use it*.

- **What it does:** Explain in the description. This is the one-line purpose.
- **When to use it:** List exhaustively in the description. These are the trigger conditions.
- **How to use it:** Explain in the body. This is the step-by-step workflow and tool reference.

Front-load trigger logic (in the description) so Claude can make intelligent routing decisions. Keep the body lean by moving reference material to subdirectories. Pair skills with MCPs for powerful integrations. Test thoroughly before deployment.

The skills you build become part of the workshop's shared toolkit. Write them clearly, test them well, and they'll amplify what everyone in the lab can do with Claude.
