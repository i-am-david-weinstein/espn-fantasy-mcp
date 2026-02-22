"""Team-related MCP tools."""
import json
from mcp.types import Tool
from espn_fantasy_mcp.espn_client import ESPNClient
from espn_fantasy_mcp.config import Config


def get_tools() -> list[Tool]:
    """Return team-related tools."""
    return [
        Tool(
            name="get_team",
            description="Get detailed information about a specific team",
            inputSchema={
                "type": "object",
                "properties": {
                    "league_id": {
                        "type": "string",
                        "description": "ESPN League ID",
                    },
                    "team_id": {
                        "type": "integer",
                        "description": "Team ID (0-based index)",
                    },
                    "season_year": {
                        "type": "integer",
                        "description": "Season year (defaults to current year)",
                    },
                },
                "required": ["team_id"],
            },
        ),
        Tool(
            name="get_roster",
            description="Get current roster for a team with player details and lineup positions",
            inputSchema={
                "type": "object",
                "properties": {
                    "league_id": {
                        "type": "string",
                        "description": "ESPN League ID",
                    },
                    "team_id": {
                        "type": "integer",
                        "description": "Team ID (0-based index)",
                    },
                    "season_year": {
                        "type": "integer",
                        "description": "Season year (defaults to current year)",
                    },
                },
                "required": ["team_id"],
            },
        ),
    ]


async def handle_tool(name: str, arguments: dict) -> str:
    """Handle team tool calls."""
    if name == "get_team":
        return await handle_get_team(arguments)
    elif name == "get_roster":
        return await handle_get_roster(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def handle_get_team(arguments: dict) -> str:
    """Handle get_team tool call."""
    league_id = arguments.get("league_id") or Config.get_default_league_id()
    team_id = arguments.get("team_id")
    season_year = arguments.get("season_year") or Config.get_default_season_year()

    if not league_id:
        raise ValueError("league_id is required")
    if team_id is None:
        raise ValueError("team_id is required")

    try:
        client = ESPNClient(
            league_id=league_id,
            season_year=season_year,
            espn_s2=Config.ESPN_S2,
            swid=Config.ESPN_SWID,
        )

        team = client.get_team(team_id)

        response = {"success": True, "data": team.to_dict()}

        return json.dumps(response, indent=2)

    except (ValueError, IndexError, KeyError, AttributeError, ConnectionError) as e:
        response = {
            "success": False,
            "error": type(e).__name__,
            "message": str(e),
        }
        return json.dumps(response, indent=2)


async def handle_get_roster(arguments: dict) -> str:
    """Handle get_roster tool call."""
    league_id = arguments.get("league_id") or Config.get_default_league_id()
    team_id = arguments.get("team_id")
    season_year = arguments.get("season_year") or Config.get_default_season_year()

    if not league_id:
        raise ValueError("league_id is required")
    if team_id is None:
        raise ValueError("team_id is required")

    try:
        client = ESPNClient(
            league_id=league_id,
            season_year=season_year,
            espn_s2=Config.ESPN_S2,
            swid=Config.ESPN_SWID,
        )

        roster = client.get_roster(team_id)

        response = {"success": True, "data": [player.to_dict() for player in roster]}

        return json.dumps(response, indent=2)

    except (ValueError, IndexError, KeyError, AttributeError, ConnectionError) as e:
        response = {
            "success": False,
            "error": type(e).__name__,
            "message": str(e),
        }
        return json.dumps(response, indent=2)
