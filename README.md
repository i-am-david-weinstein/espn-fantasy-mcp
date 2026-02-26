# ESPN Fantasy MCP Server

MCP (Model Context Protocol) server providing access to ESPN Fantasy Sports data.

NOTE: current support is limited to Fantasy Baseball

## Features

- Read league settings and configuration
- Get team information and standings
- View team rosters with player details
- Modify team lineups (move players between active slots and bench)
- Browse available free agents
- Look up players by name with fuzzy matching
- Access player statistics (actual and projected)
- View player ownership status (rostered, free agent, waivers)

## Installation and Setup

### Step 1: Get ESPN Cookies

To access private leagues, you'll need ESPN authentication cookies:

1. Login to [ESPN Fantasy Baseball](https://fantasy.espn.com/baseball/)
2. Open browser DevTools (F12 or right-click → Inspect)
3. Go to Application/Storage → Cookies → `https://fantasy.espn.com`
4. Find and copy these values:
   - `espn_s2` - Long string of characters
   - `SWID` - Format: `{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}` (includes curly braces)

### Step 2: Configure with Claude Code

Add the MCP server to Claude Code using the `claude mcp add` command. The `uvx` tool automatically manages the package installation and virtual environment. You can choose different configuration scopes:

#### Local Scope (Private to Current Project)

This stores credentials in `.claude.json` in your current directory (private to you, gitignored):

```bash
claude mcp add --transport stdio espn-fantasy \
  --env ESPN_S2=your_espn_s2_cookie \
  --env ESPN_SWID={your_espn_swid_cookie} \
  --env ESPN_LEAGUE_ID=your_league_id \
  --env ESPN_TEAM_ID=your_team_id \
  --env ESPN_SEASON_YEAR=2026 \
  -- uvx --from git+https://github.com/i-am-david-weinstein/espn-fantasy-mcp espn-fantasy-mcp
```

#### User Scope (Available Across All Projects)

This stores the configuration globally for your user account:

```bash
claude mcp add --scope user --transport stdio espn-fantasy \
  --env ESPN_S2=your_espn_s2_cookie \
  --env ESPN_SWID={your_espn_swid_cookie} \
  --env ESPN_LEAGUE_ID=your_league_id \
  --env ESPN_TEAM_ID=your_team_id \
  --env ESPN_SEASON_YEAR=2026 \
  -- uvx --from git+https://github.com/i-am-david-weinstein/espn-fantasy-mcp espn-fantasy-mcp
```

#### Project Scope (Shared via Version Control)

This creates `.mcp.json` in your repo root that can be committed and shared with your team. **Do not include sensitive credentials** in this scope:

```bash
claude mcp add --scope project --transport stdio espn-fantasy \
  --env ESPN_LEAGUE_ID=your_league_id \
  --env ESPN_TEAM_ID=your_team_id \
  --env ESPN_SEASON_YEAR=2026 \
  -- uvx --from git+https://github.com/i-am-david-weinstein/espn-fantasy-mcp espn-fantasy-mcp
```

**Important:**
- Replace the placeholder values with your actual ESPN credentials and league information
- Keep the curly braces in the SWID value: `{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}`
- No separate installation step needed - `uvx` handles package installation automatically
- `uvx` creates an isolated environment and caches the package for fast subsequent launches

### Step 3: Verify the Server is Working

After adding the server:

1. Restart Claude Code or run `/mcp` within a Claude Code session
2. Verify "espn-fantasy" appears in the MCP servers list
3. Test by asking Claude: "Show me my fantasy baseball league settings"

## Local Development Setup

If you're developing the MCP server itself:

```bash
# Clone the repository
git clone https://github.com/i-am-david-weinstein/espn-fantasy-mcp.git
cd espn-fantasy-mcp

# Install in development mode
pip install -e .

# Add to Claude Code (using local installation)
claude mcp add --transport stdio espn-fantasy \
  --env ESPN_S2=your_espn_s2_cookie \
  --env ESPN_SWID={your_espn_swid_cookie} \
  --env ESPN_LEAGUE_ID=your_league_id \
  --env ESPN_TEAM_ID=your_team_id \
  --env ESPN_SEASON_YEAR=2026 \
  -- python3 -m espn_fantasy_mcp
```

## Advanced Configuration

### Manual Configuration File

While the `claude mcp add` command is recommended, you can also manually create or edit configuration files:

**Local (`.claude.json` in project directory):**
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

**Project (`.mcp.json` in repo root, can be committed):**
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

**For Local Development (after `pip install -e .`):**
```json
{
  "mcpServers": {
    "espn-fantasy": {
      "command": "python3",
      "args": ["-m", "espn_fantasy_mcp"],
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

**Note:** With manual configuration, omit sensitive credentials from `.mcp.json` and provide them through local `.claude.json` or environment variables.

## Available Tools

### League Tools

#### `get_league_settings`
Get league configuration including scoring categories and roster settings.

**Parameters:**
- `league_id` (required): ESPN League ID
- `season_year` (optional): Season year (defaults to config)

**Example:**
```
Get league settings for league 123456
```

#### `get_standings`
Get current league standings with team records.

**Parameters:**
- `league_id` (required): ESPN League ID
- `season_year` (optional): Season year

**Example:**
```
Show me the standings for league 123456
```

### Team Tools

#### `get_team`
Get detailed information about a specific team.

**Parameters:**
- `league_id` (optional): ESPN League ID (defaults to configured league)
- `team_id` (required): Team ID (0-based index)
- `season_year` (optional): Season year

**Example:**
```
Get team info for team 0 in league 123456
```

#### `get_roster`
Get current roster for a team with player details and lineup positions.

**Parameters:**
- `league_id` (optional): ESPN League ID (defaults to configured league)
- `team_id` (required): Team ID (0-based index)
- `season_year` (optional): Season year

**Example:**
```
Show me the roster for team 0 in league 123456
```

### Player Tools

#### `get_free_agents`
Get list of available free agents on the waiver wire.

**Parameters:**
- `league_id` (required): ESPN League ID
- `season_year` (optional): Season year
- `position` (optional): Filter by position (C, 1B, 2B, SS, 3B, OF, SP, RP, P)
- `size` (optional): Number of players to return (default: 50)

**Example:**
```
Show me top 20 available shortstops in league 123456
```

#### `get_player_info`
Look up a player by name and get detailed information including stats, position, team, and roster status. Supports fuzzy matching for misspelled names.

**Parameters:**
- `player_name` (required): Player's full name (e.g., 'Shohei Ohtani', 'Aaron Judge')
- `league_id` (optional): ESPN League ID (uses default if not specified)
- `season_year` (optional): Season year (uses default if not specified)

**Example:**
```
Get info for Aaron Judge in league 123456
```

**Features:**
- Fuzzy name matching - will suggest similar names if exact match not found
- Returns player's MLB team, position, eligibility
- Shows whether player is rostered, on waivers, or a free agent
- Includes fantasy team information if player is rostered
- Returns actual and projected stats

### Roster Tools

#### `modify_lineup`
Modify team lineup by moving players between lineup slots. Uses a confirmation pattern: the first call (with `confirm=false`, the default) returns a preview of the proposed changes; the second call (with `confirm=true`) executes them. Supports moving a single player or swapping multiple players in one transaction.

**Parameters:**
- `league_id` (optional): ESPN League ID (defaults to configured league)
- `team_id` (required): Team ID (0-based index)
- `moves` (required): List of lineup moves, each containing:
  - `player_id` (required): ESPN player ID
  - `from_slot` (required): Current lineup slot ID
  - `to_slot` (required): Target lineup slot ID
- `scoring_period_id` (optional): Scoring period (week) for changes (defaults to current period)
- `season_year` (optional): Season year
- `confirm` (optional): If `false` (default), returns a preview. If `true`, executes the changes.

**Example:**
```
Move player 4140653 from bench (slot 16) to pitcher slot (slot 13) for my team
```

**Notes:**
- Always preview changes first (default behavior) before confirming
- The tool validates that each player is on the roster and currently in the specified `from_slot`
- Returns validation errors if any moves are invalid, without making any changes

## Usage Examples

Once configured with Claude Code:

```
"Show me my fantasy baseball league settings for league ID 123456"

"Who are the top 10 free agent outfielders available?"

"Get the roster for team 0 in my league"

"Show me the current standings"
```

## Response Format

All tools return JSON responses:

**Success:**
```json
{
  "success": true,
  "data": { /* tool-specific data */ }
}
```

**Error:**
```json
{
  "success": false,
  "error": "ErrorType",
  "message": "Human-readable error message"
}
```

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src/
```

### Type Checking

```bash
mypy src/
```

## Project Structure

```
espn-fantasy-mcp/
├── src/espn_fantasy_mcp/
│   ├── __init__.py
│   ├── __main__.py       # Entry point
│   ├── server.py         # MCP server
│   ├── config.py         # Configuration
│   ├── espn_client.py    # ESPN API wrapper
│   ├── models.py         # Data models
│   └── tools/            # MCP tools
│       ├── league_tools.py
│       ├── team_tools.py
│       ├── player_tools.py
│       └── roster_tools.py
├── tests/
├── docs/                 # Additional documentation
├── pyproject.toml
└── README.md
```

## Future Enhancements

- Add/drop players and trades
- Transaction history
- Additional sports (Football, Basketball, Hockey)

## Troubleshooting

**"Authentication required" error:**
- Verify ESPN_S2 and ESPN_SWID are set correctly
- Check that cookies haven't expired (re-login to ESPN)
- Ensure SWID includes curly braces `{...}`

**"League not found" error:**
- Verify league_id is correct
- Ensure you have access to the league with those credentials

**"Module not found" error:**
- Reinstall: `pip install -e .`
- Check that all `__init__.py` files exist

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

## License

MIT License

## Acknowledgments

- Built with [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- Uses [espn-api](https://github.com/cwendt94/espn-api) library
- Designed for use with Claude Code and other MCP clients
