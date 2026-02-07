# Hello World MCP: Biology Tools Server

This is a minimal MCP (Model Context Protocol) server that exposes two bioinformatics tools to Claude.

## Setup

### Option 1: Using uv (Recommended)

```bash
cd examples/mcps/01-hello-world-mcp
uv venv
source .venv/bin/activate
uv pip install -e .
```

### Option 2: Using pip

```bash
cd examples/mcps/01-hello-world-mcp
python -m venv .venv
source .venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -e .
```

## Adding to Claude Desktop

1. Open `~/.config/Claude/claude_desktop_config.json` (macOS/Linux) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

2. Add this to the `mcpServers` object:

```json
{
  "mcpServers": {
    "biology-tools": {
      "command": "python",
      "args": ["/full/path/to/examples/mcps/01-hello-world-mcp/server.py"]
    }
  }
}
```

3. Restart Claude Desktop

4. You should see a "biology-tools" option in the MCP menu (bottom left)

## Testing

### Local Test

```bash
python server.py
```

In another terminal:
```bash
python -c "
import asyncio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioClientTransport
import subprocess

async def test():
    transport = StdioClientTransport(
        subprocess.Popen(['python', 'server.py'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    )
    async with ClientSession(transport) as session:
        await session.initialize()
        result = await session.call_tool('reverse_complement', {'sequence': 'ATCG'})
        print('Result:', result)

asyncio.run(test())
"
```

### In Claude Desktop

1. Click the MCP icon (⚙️) in the bottom left
2. Select "biology-tools"
3. Ask Claude: "What is the reverse complement of ATCGATCG?"
4. Claude will call your MCP tool

## What This Teaches

**An MCP server is a standalone program that exposes tools.**

Key concepts:
- **FastMCP**: Simple decorator-based API for building MCP servers
- **Tools**: Functions decorated with `@server.tool()` that Claude can call
- **CLI integration**: MCPs are launched by Claude Desktop as subprocesses
- **JSON-RPC**: Under the hood, tools are called via JSON-RPC over stdio

This example shows the minimal viable MCP: two simple bioinformatics tools. In real projects, MCPs can:
- Query databases (GenBank, UniProt, KEGG)
- Run simulations or analyses
- Access private data or APIs
- Provide specialized domain logic

## Files

- `server.py` - The MCP server implementation
- `pyproject.toml` - Project configuration and dependencies
- `README.md` - This file
