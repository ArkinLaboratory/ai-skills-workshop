# Claude Setup Guide

Three ways to use Claude, from simplest to most powerful.

## 1. Claude Desktop (start here)

Download from [claude.ai/download](https://claude.ai/download). Sign in with your Anthropic account.

### Adding Skills

A "skill" is a markdown file that gives Claude specialized instructions. To add one:

1. Copy the skill to your skills directory:
   ```bash
   mkdir -p ~/.claude/skills/my-skill
   cp SKILL.md ~/.claude/skills/my-skill/
   ```
   This works for Claude Code, Cowork, and Claude Desktop.
2. Start a new conversation — Claude will load the skill automatically

### Adding MCP Servers

MCP servers give Claude the ability to call external tools (APIs, databases, etc.).

Use the CLI to register a server:

```bash
claude mcp add --scope user my-server python /path/to/server.py
```

This writes the config for you — no manual JSON editing required. The `--scope user` flag makes it available across all your projects.

To see registered servers:
```bash
claude mcp list
```

To remove one:
```bash
claude mcp remove --scope user my-server
```

Restart Claude Desktop after adding or removing servers.

## 2. Claude Code (command line)

For coders who prefer the terminal.

```bash
# Install
npm install -g @anthropic-ai/claude-code

# Run
claude
```

Claude Code also uses the same CLI command to register MCP servers:

```bash
claude mcp add --scope user my-server python /path/to/server.py
```

This works seamlessly across Claude Code, Cowork, and Claude Desktop — no manual config file editing needed.

## 3. Anthropic API (programmatic)

For Python scripts, notebooks, and automated pipelines.

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

```python
import anthropic

client = anthropic.Anthropic()
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "What is a bacteriophage?"}],
)
print(message.content[0].text)
```

Get your API key from [console.anthropic.com](https://console.anthropic.com/).

## Alternative: Use CBORG Instead

For work with sensitive pre-publication data, or to avoid personal API costs,
use [CBORG](cborg.md). CBORG provides Claude Sonnet/Haiku via an
OpenAI-compatible API at no cost to @lbl.gov users.

## Key References

- [MCP Docs: Build a Server](https://modelcontextprotocol.io/docs/develop/build-server)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
