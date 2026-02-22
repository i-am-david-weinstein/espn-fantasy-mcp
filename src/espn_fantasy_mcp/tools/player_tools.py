"""Player-related MCP tools."""
import json
from mcp.types import Tool
from espn_fantasy_mcp.espn_client import ESPNClient
from espn_fantasy_mcp.config import Config


def get_tools() -> list[Tool]:
    """Return player-related tools."""
    return [
        Tool(
            name="get_free_agents",
            description="Get list of available free agents on the waiver wire",
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
                    "position": {
                        "type": "string",
                        "description": "Filter by position (C, 1B, 2B, SS, 3B, OF, SP, RP, P)",
                    },
                    "size": {
                        "type": "integer",
                        "description": "Number of players to return (default: 50)",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_player_info",
            description="Look up a player by name and get detailed information including stats, position, team, and roster status. Supports fuzzy matching for misspelled names.",
            inputSchema={
                "type": "object",
                "properties": {
                    "player_name": {
                        "type": "string",
                        "description": "Player's full name (e.g., 'Shohei Ohtani', 'Aaron Judge')",
                    },
                    "league_id": {
                        "type": "string",
                        "description": "ESPN League ID",
                    },
                    "season_year": {
                        "type": "integer",
                        "description": "Season year (defaults to current year)",
                    },
                },
                "required": ["player_name"],
            },
        ),
    ]


async def handle_tool(name: str, arguments: dict) -> str:
    """Handle player tool calls."""
    if name == "get_free_agents":
        return await handle_get_free_agents(arguments)
    elif name == "get_player_info":
        return await handle_get_player_info(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def handle_get_free_agents(arguments: dict) -> str:
    """Handle get_free_agents tool call."""
    league_id = arguments.get("league_id") or Config.get_default_league_id()
    season_year = arguments.get("season_year") or Config.get_default_season_year()
    position = arguments.get("position")
    size = arguments.get("size", 50)

    if not league_id:
        raise ValueError("league_id is required")

    try:
        client = ESPNClient(
            league_id=league_id,
            season_year=season_year,
            espn_s2=Config.ESPN_S2,
            swid=Config.ESPN_SWID,
        )

        free_agents = client.get_free_agents(size=size, position=position)

        response = {"success": True, "data": [player.to_dict() for player in free_agents]}

        return json.dumps(response, indent=2)

    except (ValueError, IndexError, KeyError, AttributeError, ConnectionError) as e:
        response = {
            "success": False,
            "error": type(e).__name__,
            "message": str(e),
        }
        return json.dumps(response, indent=2)


async def handle_get_player_info(arguments: dict) -> str:
    """Handle get_player_info tool call."""
    player_name = arguments.get("player_name")
    league_id = arguments.get("league_id") or Config.get_default_league_id()
    season_year = arguments.get("season_year") or Config.get_default_season_year()

    if not player_name:
        raise ValueError("player_name is required")

    if not league_id:
        raise ValueError("league_id is required")

    try:
        client = ESPNClient(
            league_id=league_id,
            season_year=season_year,
            espn_s2=Config.ESPN_S2,
            swid=Config.ESPN_SWID,
        )

        player, suggestions = client.get_player_by_name(player_name)

        if player:
            response = {
                "success": True,
                "data": player.to_dict(),
            }
        else:
            # Player not found, return suggestions
            response = {
                "success": False,
                "error": "PlayerNotFound",
                "message": f"Player '{player_name}' not found",
                "suggestions": suggestions,
            }

        return json.dumps(response, indent=2)

    except (ValueError, IndexError, KeyError, AttributeError, ConnectionError) as e:
        response = {
            "success": False,
            "error": type(e).__name__,
            "message": str(e),
        }
        return json.dumps(response, indent=2)
