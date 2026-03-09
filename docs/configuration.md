# Configuration

## Installation Scopes

`claude mcp add` supports three scopes. Choose based on whether you want credentials private to you or shared with a team.

### User scope (recommended for personal use)

Stored globally in your user account. Available in all projects.

```bash
claude mcp add --scope user --transport stdio espn-fantasy \
  --env ESPN_S2=your_espn_s2_cookie \
  --env ESPN_SWID={your_espn_swid_cookie} \
  --env ESPN_LEAGUE_ID=your_league_id \
  --env ESPN_TEAM_ID=your_team_id \
  --env ESPN_SEASON_YEAR=2026 \
  -- uvx --from git+https://github.com/i-am-david-weinstein/espn-fantasy-mcp espn-fantasy-mcp
```

### Local scope

Stored in `.claude.json` in your current directory. Private to you (gitignored).

```bash
claude mcp add --transport stdio espn-fantasy \
  --env ESPN_S2=your_espn_s2_cookie \
  --env ESPN_SWID={your_espn_swid_cookie} \
  --env ESPN_LEAGUE_ID=your_league_id \
  --env ESPN_TEAM_ID=your_team_id \
  --env ESPN_SEASON_YEAR=2026 \
  -- uvx --from git+https://github.com/i-am-david-weinstein/espn-fantasy-mcp espn-fantasy-mcp
```

### Project scope

Stored in `.mcp.json` in your repo root. Can be committed and shared. **Do not include `ESPN_S2` or `ESPN_SWID` here** — provide those via local scope or environment variables.

```bash
claude mcp add --scope project --transport stdio espn-fantasy \
  --env ESPN_LEAGUE_ID=your_league_id \
  --env ESPN_TEAM_ID=your_team_id \
  --env ESPN_SEASON_YEAR=2026 \
  -- uvx --from git+https://github.com/i-am-david-weinstein/espn-fantasy-mcp espn-fantasy-mcp
```

---

## Manual Configuration

If you prefer to edit config files directly instead of using `claude mcp add`:

**User/local** (`.claude.json`):
```json
{
  "mcpServers": {
    "espn-fantasy": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/i-am-david-weinstein/espn-fantasy-mcp",
        "espn-fantasy-mcp"
      ],
      "env": {
        "ESPN_S2": "your_espn_s2_cookie",
        "ESPN_SWID": "{your_espn_swid_cookie}",
        "ESPN_LEAGUE_ID": "your_league_id",
        "ESPN_TEAM_ID": "your_team_id",
        "ESPN_SEASON_YEAR": "2026"
      }
    }
  }
}
```

**Project** (`.mcp.json`, omit credentials):
```json
{
  "mcpServers": {
    "espn-fantasy": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/i-am-david-weinstein/espn-fantasy-mcp",
        "espn-fantasy-mcp"
      ],
      "env": {
        "ESPN_LEAGUE_ID": "your_league_id",
        "ESPN_TEAM_ID": "your_team_id",
        "ESPN_SEASON_YEAR": "2026"
      }
    }
  }
}
```

---

## Troubleshooting

**"Authentication required" error**
- Verify `ESPN_S2` and `ESPN_SWID` are set correctly
- Cookies expire — re-login to ESPN and copy fresh values
- Ensure `SWID` includes curly braces: `{XXXXXXXX-...}`

**"League not found" error**
- Verify `ESPN_LEAGUE_ID` is correct (found in the league URL)
- Confirm your account has access to that league
