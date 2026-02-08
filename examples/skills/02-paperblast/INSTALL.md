# Installing the PaperBLAST Skill

This skill gives Claude access to [PaperBLAST](https://papers.genomics.lbl.gov),
Curated BLAST, and GapMind via an MCP (Model Context Protocol) server.
It works with both **Claude Code** and **Cowork** (Claude Desktop).

## Prerequisites

- Python 3.10 or later
- `pip` (Python package manager)
- **Requires LBNL VPN** — papers.genomics.lbl.gov is behind Cloudflare
  and blocks non-LBL IP addresses.

## Setting Up the LBNL VPN

PaperBLAST requires a connection to the LBNL network. If you're not on-site
(wired or LBL WiFi), you need the Cisco AnyConnect VPN client.

**Install (one-time):**

1. Go to [software.lbl.gov](https://software.lbl.gov) and log in with your
   Berkeley Lab identity
2. Search for **"VPN"** and select **Cisco VPN**
3. Download **Cisco VPN for macOS** (or your OS) from the Current Releases section
4. Run the installer. On macOS you may need to:
   - Right-click the `.pkg` → Open With → Installer if Gatekeeper blocks it
   - Allow the Cisco AnyConnect kernel extension in
     **System Preferences → Privacy & Security** when prompted
5. The installed app appears as **Cisco Secure Client** (or **Cisco AnyConnect**)
   in your Applications folder

**Connect:**

1. Launch Cisco Secure Client
2. Enter the VPN server address if prompted (check [LBNL VPN info](https://commons.lbl.gov/spaces/itfaq/pages/132810873/VPN+Information) for the current address)
3. Authenticate with your LBNL LDAP credentials
4. Once connected, verify with:

```bash
curl -s -o /dev/null -w "%{http_code}" https://papers.genomics.lbl.gov
# Should print: 200
```

If you see `403` or `000`, your VPN is not connected.

## Step 1 — Install Python dependencies

```bash
pip install httpx beautifulsoup4 lxml pydantic "mcp[cli]"
```

## Step 2 — Run the dependency checker

From inside the skill directory:

```bash
cd examples/skills/02-paperblast
python3 scripts/check_deps.py --live
```

You should see `ALL CHECKS PASSED` and a successful live connectivity test.
If the live test fails with a Cloudflare challenge or 403 error, your VPN connection may not be active. Verify you are connected to the LBNL VPN before proceeding.

## Step 3 — Copy the skill into Claude's skills directory

Claude reads skills from `~/.claude/skills/<skill-name>/`. From the skill
directory (`examples/skills/02-paperblast/`), copy the necessary files:

```bash
mkdir -p ~/.claude/skills/paperblast/scripts

# From examples/skills/02-paperblast/:
cp SKILL.md                   ~/.claude/skills/paperblast/
cp scripts/paperblast_mcp.py  ~/.claude/skills/paperblast/scripts/
cp scripts/models.py          ~/.claude/skills/paperblast/scripts/
```

This gives Claude the SKILL.md (workflow guidance) and the MCP server
code (paperblast_mcp.py + its Pydantic models).

## Step 4 — Register the MCP server

The MCP server must be registered so Claude can invoke its tools.
Use `claude mcp add` with `--scope user` so it's available in every session:

```bash
claude mcp add --scope user paperblast \
  python3 \
  ~/.claude/skills/paperblast/scripts/paperblast_mcp.py
```

> **Note:** If your Python 3.10+ is not on `PATH` as `python3`, use the full
> path (e.g., `/opt/anaconda3/bin/python3`). The Python that runs the MCP
> server must have the dependencies from Step 1 installed.

You should see:

```
Added stdio MCP server paperblast ...
paperblast: ... ✓ Connected
```

## Step 5 — Verify

```bash
claude mcp list
```

Should show `paperblast` with its command and path.

## Step 6 — Test in Claude Code

Start (or restart) Claude Code and try a natural query:

```
Search PaperBLAST for MinD (P0AEZ3)
```

Claude should invoke the `paperblast_search` MCP tool and return structured
results with gene entries, paper snippets, and similarity metrics.

Other test queries:

- `Use Curated BLAST to find alcohol dehydrogenases in E. coli K-12`
- `Check GapMind amino acid biosynthesis for Pseudomonas fluorescens`
- `List organisms available in GapMind for carbon source utilization`

## Updating the skill

When the repo is updated, pull the latest code and re-copy:

```bash
git pull
cp examples/skills/02-paperblast/SKILL.md          ~/.claude/skills/paperblast/
cp examples/skills/02-paperblast/scripts/paperblast_mcp.py ~/.claude/skills/paperblast/scripts/
cp examples/skills/02-paperblast/scripts/models.py         ~/.claude/skills/paperblast/scripts/
```

The MCP registration persists — no need to re-run `claude mcp add`.
Restart Claude Code to pick up the new server code.

## Uninstalling

```bash
claude mcp remove paperblast
rm -rf ~/.claude/skills/paperblast
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `claude mcp list` shows nothing | MCP not registered | Run Step 4 again |
| `✗ Failed to connect` on add | Python can't import deps | Run Step 2 to diagnose |
| Cloudflare challenge / 403 | Network blocked | Connect to LBNL VPN |
| Claude uses Bash instead of MCP tools | MCP server not connected | Check `claude mcp list`; restart Claude Code |
| `ModuleNotFoundError: models` | models.py not copied | Ensure models.py is next to paperblast_mcp.py |
| Results look wrong or empty | Page structure may have changed | Check the URL in output against the live site |

## File inventory

```
02-paperblast/
├── INSTALL.md            ← You are here
├── SKILL.md              ← Workflow guidance Claude reads at runtime
├── TESTING.md            ← How to run and interpret parser tests
├── USAGE-EXAMPLES.md     ← Worked examples with real output
├── README.md             ← Skill overview
├── pyproject.toml        ← Dependency metadata
├── references/
│   └── setup.md          ← Extended setup notes and future tools
└── scripts/
    ├── paperblast_mcp.py ← MCP server (5 tools + HTML parsers)
    ├── models.py         ← Pydantic output models (13 models)
    ├── test_parser.py    ← Live parser tests
    └── check_deps.py     ← Dependency diagnostic
```
