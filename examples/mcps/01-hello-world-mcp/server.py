"""
Minimal MCP server with two biology tools.

This teaches:
- How to define an MCP server using FastMCP
- How to expose tools that Claude can call
- Basic bioinformatics functions (reverse complement, GC content)

Installation:
    pip install mcp[cli] anthropic httpx
    # or with uv:
    uv pip install mcp[cli] anthropic httpx

Running locally:
    python server.py

Testing:
    # In another terminal, test the server:
    python -c "
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioClientTransport
import subprocess
import asyncio

async def test():
    transport = StdioClientTransport(
        subprocess.Popen(
            ['python', 'server.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    )
    async with ClientSession(transport) as session:
        await session.initialize()
        result = await session.call_tool('reverse_complement', {'sequence': 'ATCG'})
        print('reverse_complement(ATCG):', result)
        result = await session.call_tool('gc_content', {'sequence': 'ATGCATGC'})
        print('gc_content(ATGCATGC):', result)

asyncio.run(test())
    "
"""

from mcp.server.fastmcp import FastMCP

# Create the server
server = FastMCP("biology-tools")


@server.tool()
def reverse_complement(sequence: str) -> str:
    """
    Reverse complement a DNA sequence.

    Args:
        sequence: DNA sequence (ATCG)

    Returns:
        Reverse complement of the sequence
    """
    complement = {"A": "T", "T": "A", "C": "G", "G": "C"}
    return "".join(complement.get(base, "N") for base in reversed(sequence))


@server.tool()
def gc_content(sequence: str) -> float:
    """
    Calculate GC content (% of G and C bases) in a DNA sequence.

    Args:
        sequence: DNA sequence (ATCG)

    Returns:
        GC content as a percentage (0-100)
    """
    if len(sequence) == 0:
        return 0.0
    gc_count = sequence.count("G") + sequence.count("C")
    return (gc_count / len(sequence)) * 100


if __name__ == "__main__":
    server.run()
