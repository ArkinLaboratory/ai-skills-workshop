#!/usr/bin/env python3
"""
Quick diagnostic to verify PaperBLAST MCP server dependencies.
Run this before adding the server to settings.json.

Usage:
    python3 check_deps.py          # check imports only
    python3 check_deps.py --live   # also test live HTTP to papers.genomics.lbl.gov
"""
import sys

print(f"Python: {sys.executable} ({sys.version})")
print()

errors = []

# --- Check imports ---
deps = {
    "httpx": "pip install httpx",
    "bs4": "pip install beautifulsoup4",
    "lxml": "pip install lxml",
    "pydantic": "pip install pydantic",
    "mcp": 'pip install "mcp[cli]"',
}

for module, install_cmd in deps.items():
    try:
        mod = __import__(module)
        ver = getattr(mod, "__version__", "?")
        print(f"  OK  {module:12s}  v{ver}")
    except ImportError:
        print(f" FAIL {module:12s}  -> {install_cmd}")
        errors.append(module)

# Check specific import path used by the server
print()
try:
    from mcp.server.fastmcp import FastMCP
    print("  OK  mcp.server.fastmcp.FastMCP import works")
except ImportError as e:
    print(f" FAIL mcp.server.fastmcp.FastMCP: {e}")
    print("      You may need a newer version: pip install --upgrade 'mcp[cli]'")
    errors.append("FastMCP")
except Exception as e:
    print(f" FAIL mcp.server.fastmcp.FastMCP: {type(e).__name__}: {e}")
    errors.append("FastMCP")

# --- Check server script loads ---
print()
try:
    import importlib.util
    import os
    script = os.path.join(os.path.dirname(__file__), "paperblast_mcp.py")
    if os.path.exists(script):
        spec = importlib.util.spec_from_file_location("paperblast_mcp", script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        print(f"  OK  paperblast_mcp.py loads without error")
        # Check registered tools
        if hasattr(mod, 'mcp') and hasattr(mod.mcp, '_tools'):
            tools = list(mod.mcp._tools.keys()) if hasattr(mod.mcp._tools, 'keys') else []
            print(f"      Registered tools: {tools}")
    else:
        print(f" WARN paperblast_mcp.py not found at {script}")
except Exception as e:
    print(f" FAIL paperblast_mcp.py load error: {type(e).__name__}: {e}")
    errors.append("server_load")

# --- Optional live test ---
if "--live" in sys.argv:
    print()
    print("--- Live connectivity test ---")
    import asyncio

    async def test_live():
        import httpx
        from bs4 import BeautifulSoup
        try:
            async with httpx.AsyncClient(timeout=60, follow_redirects=True) as c:
                r = await c.get(
                    "https://papers.genomics.lbl.gov/cgi-bin/litSearch.cgi",
                    params={"query": "P0AEZ3"}
                )
                print(f"  Status: {r.status_code}")
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, "lxml")
                    title = soup.find("title")
                    print(f"  Title: {title.text.strip() if title else 'N/A'}")
                    # Check for Cloudflare challenge
                    if "Just a moment" in (title.text if title else ""):
                        print("  WARN  Cloudflare challenge detected! Are you on LBL VPN?")
                    else:
                        pubmed = soup.find_all("a", href=lambda h: h and "pubmed" in h)
                        print(f"  PubMed links: {len(pubmed)}")
                        print("  OK  Live connection works")
                elif r.status_code == 403:
                    print("  FAIL  403 Forbidden — likely Cloudflare. Connect to LBL VPN.")
        except Exception as e:
            print(f"  FAIL  {type(e).__name__}: {e}")

    asyncio.run(test_live())

# --- Summary ---
print()
if errors:
    print(f"FAILED: {len(errors)} issue(s). Fix the above before adding to settings.json.")
    print(f"Quick fix: pip install httpx beautifulsoup4 lxml 'mcp[cli]'")
    sys.exit(1)
else:
    print("ALL CHECKS PASSED. Safe to add to settings.json.")
    sys.exit(0)
