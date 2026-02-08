# What Is a Skill?

A **skill** is a markdown file (`SKILL.md`) that gives Claude specialized instructions for a specific domain or task. Think of it as a detailed system prompt that you can install, share, and reuse.

## How It Works

1. You place a `SKILL.md` file in Claude's skills directory
2. When you start a conversation, Claude reads the skill and follows its instructions
3. The skill can tell Claude about domain knowledge, workflow patterns, tools, and constraints

For Claude Code and Cowork, the skills directory is `~/.claude/skills/`. Create a subdirectory for each skill (e.g., `~/.claude/skills/my-skill/SKILL.md`).

## What a Skill Can Do

- Teach Claude about your lab's specific tools and databases
- Define step-by-step workflows (e.g., "to annotate a protein, first search PaperBLAST, then...")
- Provide domain vocabulary and conventions
- Set output format expectations

## What a Skill Cannot Do

- Call external APIs or databases directly (that's what MCPs do)
- Execute code
- Access files on your computer
- Remember things between conversations

## Skill vs MCP: When to Use Which

| Need | Use a Skill | Use an MCP |
|------|-------------|-----------|
| Give Claude domain knowledge | Yes | No |
| Call an external API | No | Yes |
| Define a workflow | Yes | No |
| Execute code/queries | No | Yes |
| Share as a single file | Yes | Harder |

**Best practice:** Use skills and MCPs together. The skill teaches Claude *what* to do and *when*. The MCP gives Claude the *ability* to do it.

## Example

The [PaperBLAST skill](../examples/skills/02-paperblast/) combines both:
- `SKILL.md` teaches Claude about PaperBLAST, Curated BLAST, and GapMind — what they are, when to use each, and how to interpret results
- `scripts/paperblast_mcp.py` is an MCP server that actually makes HTTP requests to papers.genomics.lbl.gov and parses the HTML responses

## Anatomy of a SKILL.md

```markdown
---
name: my-skill
description: >
  When to trigger this skill: (1) user asks about X,
  (2) user mentions Y, (3) user wants to do Z.
---

# My Skill Name

## Available Tools (if paired with an MCP)
| Tool | When to use | Input |
|------|-------------|-------|

## Workflow Patterns
### Pattern 1: Do X
1. First step
2. Second step

## Domain Knowledge
Key facts Claude needs to know.

## Query Tips
Common patterns and gotchas.
```

## Next: Try It

Go to [examples/skills/01-hello-world/](../examples/skills/01-hello-world/) and install your first skill.
