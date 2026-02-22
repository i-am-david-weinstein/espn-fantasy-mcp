"""League-related MCP tools."""
import json
from mcp.types import Tool
from espn_fantasy_mcp.espn_client import ESPNClient
from espn_fantasy_mcp.config import Config


def get_tools() -> list[Tool]:
    """Return league-related tools."""
    return [
        Tool(
            name="get_league_settings",
            description="Get league configuration including scoring categories, roster settings, and league rules",
            inputSchema={
                "type": "object",
                "properties": {
                    "league_id": {
                        "type": "string",
                        "description": "ESPN League ID (found in league URL)",
                    },
                    "season_year": {
                        "type": "integer",
                        "description": "Season year (defaults to current year if not specified)",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_standings",
            description="Get current league standings with team records and rankings",
            inputSchema={
                "type": "object",
                "properties": {
                    "league_id": {
                        "type": "string",
                        "description": "ESPN League ID",
                    },
                    "season_year": {
                        "type": "integer",
                        "description": "Season year (defaults to current year)",
                    },
                },
                "required": [],
            },
        ),
    ]


async def handle_tool(name: str, arguments: dict) -> str:
    """Handle league tool calls."""
    if name == "get_league_settings":
        return await handle_get_league_settings(arguments)
    elif name == "get_standings":
        return await handle_get_standings(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def handle_get_league_settings(arguments: dict) -> str:
    """Handle get_league_settings tool call."""
    league_id = arguments.get("league_id") or Config.get_default_league_id()
    season_year = arguments.get("season_year") or Config.get_default_season_year()

    if not league_id:
        raise ValueError("league_id is required")

    try:
        client = ESPNClient(
            league_id=league_id,
            season_year=season_year,
            espn_s2=Config.ESPN_S2,
            swid=Config.ESPN_SWID,
        )

        settings = client.get_league_settings()

        response = {"success": True, "data": settings.to_dict()}

        return json.dumps(response, indent=2)

    except (ValueError, IndexError, KeyError, AttributeError, ConnectionError) as e:
        response = {
            "success": False,
            "error": type(e).__name__,
            "message": str(e),
        }
        return json.dumps(response, indent=2)


async def handle_get_standings(arguments: dict) -> str:
    """Handle get_standings tool call."""
    league_id = arguments.get("league_id") or Config.get_default_league_id()
    season_year = arguments.get("season_year") or Config.get_default_season_year()

    if not league_id:
        raise ValueError("league_id is required")

    try:
        client = ESPNClient(
            league_id=league_id,
            season_year=season_year,
            espn_s2=Config.ESPN_S2,
            swid=Config.ESPN_SWID,
        )

        standings = client.get_standings()

        response = {"success": True, "data": [team.to_dict() for team in standings]}

        return json.dumps(response, indent=2)

    except (ValueError, IndexError, KeyError, AttributeError, ConnectionError) as e:
        response = {
            "success": False,
            "error": type(e).__name__,
            "message": str(e),
        }
        return json.dumps(response, indent=2)
