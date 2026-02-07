# AI Skills Workshop

Learn to build AI skills and MCP (Model Context Protocol) servers for biological research.

Part of the [Arkin Lab Hack-a-thon](https://github.com/ArkinLaboratory/handbook/tree/main/hackathon).

## What's Here

| Folder | Contents |
|--------|----------|
| `docs/` | Concepts: what are skills, MCPs, how they differ |
| `examples/skills/` | Working skill examples, simplest to most complex |
| `examples/mcps/` | Working MCP server examples |
| `examples/python-calling/` | Calling Claude programmatically from Python |
| `templates/` | Starter templates for new skills and MCPs |
| `setup/` | Environment setup and config examples |

## Prerequisites

- [Claude Desktop](https://github.com/ArkinLaboratory/handbook/blob/main/ai-resources/claude-setup.md) installed
- For MCP development: Python >= 3.10, [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager
- For API examples: Anthropic API key or [CBORG API key](https://github.com/ArkinLaboratory/handbook/blob/main/ai-resources/cborg.md)

## Quick Start

### 1. Try a skill (no code, 5 minutes)

Copy `examples/skills/01-hello-world/SKILL.md` into your Claude Desktop skills folder. Start a new conversation and ask a biology question.

### 2. Run an MCP server (Python, 15 minutes)

```bash
cd examples/mcps/01-hello-world-mcp
uv run server.py
```

Then add it to your Claude Desktop config. See the [README](examples/mcps/01-hello-world-mcp/README.md) for details.

### 3. Call Claude from Python (15 minutes)

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...  # or use CBORG
python examples/python-calling/01-basic-api-call.py
```

## Session Schedule

| Session | Topic | Materials |
|---------|-------|-----------|
| 1 (done) | Orientation | — |
| 2 (next) | Skills Deep Dive | `examples/skills/`, `docs/what-is-a-skill.md` |
| 3 | MCP Foundations | `examples/mcps/`, `docs/what-is-an-mcp.md` |
| 4 | Build Your Own | `templates/`, [AI 101 task list](https://docs.google.com/document/d/1hrDxWMo3VsT7PPKdj76HYF9TTq5CIgWl2aJs88dlGGU/edit) |
| 5 | Lakehouse + Integration | Lakehouse MCP examples |
| 6 | Show & Tell | Demos and retrospective |

## Key References

- [MCP Official Docs: Build a Server](https://modelcontextprotocol.io/docs/develop/build-server)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp) (Python MCP framework)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python)
- [CBORG API Examples](https://cborg.lbl.gov/api_examples/)

## Existing Lakehouse Tools (reference)

| Tool | What It Does | Repo |
|------|-------------|------|
| BERDL-ENIGMA-CORAL | DuckDB MCP for ENIGMA data | [jmchandonia](https://github.com/jmchandonia/BERDL-ENIGMA-CORAL) |
| lakehouse-skills | Claude skills for KBase/JGI | [cmungall](https://github.com/cmungall/lakehouse-skills) |
| lakehouse-chat | NL→SQL chat for BERDL | [justaddcoffee](https://github.com/justaddcoffee/lakehouse-chat) |
