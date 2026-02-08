# Hello World Skill: Haiku Microbiology Responder

This is the simplest possible skill to teach how Claude can adopt personas and constraints.

## Installation

### Option A: Claude Code / Cowork (CLI)

```bash
mkdir -p ~/.claude/skills/haiku-bio
cp SKILL.md ~/.claude/skills/haiku-bio/
```

Start a new session — Claude will load the skill automatically.

### Option B: Claude Desktop (GUI)

1. Open Claude Desktop
2. Click **Claude** menu → **Settings** → **Developer**
3. Click the folder icon next to "Skills"
4. Navigate to this directory (`examples/skills/01-hello-world/`)
5. Select the folder and confirm

## What to Expect

When you add this skill:
- Claude will respond to biology questions with a haiku first
- Then provide the actual detailed answer
- The skill persists only during that conversation

Try asking Claude questions like:
- "What is photosynthesis?"
- "Explain DNA replication"
- "What do mitochondria do?"

## What This Teaches

**A skill is just a markdown file.** That's it.

The key insight: Skills work by embedding instructions in the frontmatter and markdown. This example shows:
- **Frontmatter** (`---` blocks): Store metadata (name, description)
- **Instructions**: Plain markdown text that guides Claude's behavior
- **Examples**: Markdown showing what good output looks like

No code. No API calls. Just creative prompting bundled in a shareable file.

Skills are the lightest-weight way to customize Claude's behavior per conversation.

## Files

- `SKILL.md` - The skill definition itself (loaded by Claude Desktop)
- `README.md` - This file
