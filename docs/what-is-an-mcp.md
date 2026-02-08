# What Is an MCP Server?

**MCP** (Model Context Protocol) is a standard that lets Claude (and other LLMs) call external tools — APIs, databases, file systems, anything with a programmatic interface.

An **MCP server** is a small program (usually Python) that exposes one or more **tools** that Claude can call during a conversation.

## How It Works

```
You ask Claude a question
    ↓
Claude decides it needs data from an external source
    ↓
Claude calls a tool exposed by your MCP server
    ↓
The MCP server executes the request (API call, DB query, etc.)
    ↓
Results go back to Claude
    ↓
Claude synthesizes an answer using the results
```

## Analogy

If Claude is a researcher, an MCP server is like giving them access to a lab instrument. The skill (SKILL.md) is the protocol manual that tells them when and how to use it.

## What an MCP Server Looks Like

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("My Server")

@mcp.tool()
def reverse_complement(sequence: str) -> str:
    """Return the reverse complement of a DNA sequence."""
    complement = {"A": "T", "T": "A", "C": "G", "G": "C"}
    return "".join(complement.get(b, b) for b in reversed(sequence.upper()))

if __name__ == "__main__":
    mcp.run()
```

That's it. The `@mcp.tool()` decorator registers a Python function as something Claude can call. FastMCP automatically generates the tool schema from the type hints and docstring.

## MCP vs REST API vs Python Library

| | MCP Server | REST API | Python Library |
|--|-----------|---------|----------------|
| Who calls it? | Claude (automatically) | Your code (manually) | Your code (manually) |
| Discovery | Claude sees available tools | You read docs | You read docs |
| Input validation | Automatic (from type hints) | Manual | Manual |
| Works in Claude Desktop | Yes | No (need MCP wrapper) | No |

## How to Connect an MCP Server to Claude

Register your server using the CLI:

```bash
claude mcp add --scope user my-server python /path/to/server.py
```

This works for Claude Code, Cowork, and Claude Desktop. The `--scope user` flag makes the server available across all your projects.

To verify it's registered:
```bash
claude mcp list
```

To remove a server:
```bash
claude mcp remove --scope user my-server
```

After adding or removing a server, restart Claude Desktop (or start a new Claude Code session).

> **Note:** If you need to use `uv` instead of `python` directly, that works too:
> ```bash
> claude mcp add --scope user my-server uv run --directory /path/to/server server.py
> ```

## MCP Scopes: Personal vs Team

MCP servers can be registered at three different scopes:

### `--scope local` (default)
Personal to you, specific to one project. Config lives in `.claude/settings.local.json`. Not version-controlled. Use for experimental or project-specific tools you don't want to share.

### `--scope project`
Team-shared. Creates `.mcp.json` in the project root. Commit this to version control. Everyone who clones the repo gets the MCP automatically. **Claude prompts for user approval on first use** (security measure). Best for workshop MCPs and team collaboration.

```bash
claude mcp add --scope project paperblast python3 scripts/paperblast_mcp.py
```

### `--scope user`
Personal, cross-project. Stored in `~/.claude.json`. Available everywhere. Good for personal tools you use across many projects.

### Environment Variables

You can pass environment variables when registering:

```bash
claude mcp add --scope user my-server --env API_KEY=abc123 python server.py
```

### For This Hackathon

- Use `--scope project` for shared workshop MCPs that teammates need
- Use `--scope user` for personal tools you want across projects
- Commit `.mcp.json` to version control so teammates get the tools automatically

## Key Concepts

- **Tool**: A single function Claude can call (e.g., `reverse_complement`)
- **Server**: A program that exposes one or more tools
- **Transport**: How Claude talks to the server (usually `stdio` for local, `streamable-http` for remote)
- **FastMCP**: The Python framework that makes building servers easy

## Key References

- [Official MCP Docs: Build a Server](https://modelcontextprotocol.io/docs/develop/build-server)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

## Next: Build One

Go to [examples/mcps/01-hello-world-mcp/](../examples/mcps/01-hello-world-mcp/) and build your first MCP server.
