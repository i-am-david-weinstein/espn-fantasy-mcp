# ESPN Fantasy MCP Server

[![Tests](https://github.com/i-am-david-weinstein/espn-fantasy-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/i-am-david-weinstein/espn-fantasy-mcp/actions/workflows/test.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

MCP (Model Context Protocol) server providing access to ESPN Fantasy Baseball data, for use with Claude Code and other MCP clients.

## Features

- Read league settings, standings, and team information
- View rosters with player details and lineup positions
- Look up players by name with fuzzy matching
- Browse and add free agents, submit waiver claims
- Modify lineups
- Propose, accept, decline, and cancel trades

## Quick Start

### 1. Get ESPN Cookies

To access private leagues, you need ESPN authentication cookies:

1. Log in to [ESPN Fantasy Baseball](https://fantasy.espn.com/baseball/)
2. Open browser DevTools → Application → Cookies → `https://fantasy.espn.com`
3. Copy `espn_s2` (long string) and `SWID` (format: `{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}`)

### 2. Add to Claude Code

```bash
claude mcp add --scope user --transport stdio espn-fantasy \
  --env ESPN_S2=your_espn_s2_cookie \
  --env ESPN_SWID={your_espn_swid_cookie} \
  --env ESPN_LEAGUE_ID=your_league_id \
  --env ESPN_TEAM_ID=your_team_id \
  --env ESPN_SEASON_YEAR=2026 \
  -- uvx --from git+https://github.com/i-am-david-weinstein/espn-fantasy-mcp espn-fantasy-mcp
```

Keep the curly braces in the SWID value. `uvx` handles installation automatically — no separate install step needed.

### 3. Verify

Restart Claude Code or run `/mcp` and confirm "espn-fantasy" appears in the server list. Then try: *"Show me my fantasy baseball league settings"*

## Documentation

- [Tool Reference](docs/tools.md) — all available tools and parameters
- [Configuration](docs/configuration.md) — scopes, manual config, troubleshooting

## Local Development

```bash
git clone https://github.com/i-am-david-weinstein/espn-fantasy-mcp.git
cd espn-fantasy-mcp
pip install -e ".[dev]"
pytest
```

To use a local install with Claude Code, replace the `uvx ...` portion of the `claude mcp add` command with `python3 -m espn_fantasy_mcp`.

## Contributing

Contributions welcome — open an issue or submit a pull request.

## License

MIT

## Acknowledgments

- Built with [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- Uses [espn-api](https://github.com/cwendt94/espn-api)
