# Claude Setup Guide

Three ways to use Claude, from simplest to most powerful.

## 1. Claude Desktop (start here)

Download from [claude.ai/download](https://claude.ai/download). Sign in with your Anthropic account.

### Adding Skills

A "skill" is a markdown file that gives Claude specialized instructions. To add one:

1. Find your skills directory:
   - macOS: `~/Library/Application Support/Claude/`
   - Create a folder for the skill (e.g., `paperblast-skill/`)
2. Place the `SKILL.md` file inside
3. Start a new conversation — Claude will use the skill automatically

### Adding MCP Servers

MCP servers give Claude the ability to call external tools (APIs, databases, etc.).

Edit `claude_desktop_config.json`:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "paperblast": {
      "command": "python",
      "args": ["/path/to/paperblast-skill/scripts/paperblast_mcp.py"]
    }
  }
}
```

Restart Claude Desktop after editing.

## 2. Claude Code (command line)

For coders who prefer the terminal.

```bash
# Install
npm install -g @anthropic-ai/claude-code

# Run
claude
```

Claude Code reads MCP config from `~/.claude/settings.json` or per-project `.claude/settings.json`:

```json
{
  "mcpServers": {
    "paperblast": {
      "command": "python",
      "args": ["/path/to/paperblast-skill/scripts/paperblast_mcp.py"]
    }
  }
}
```

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
