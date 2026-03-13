"""Player-related MCP tools."""

import json
from espn_fantasy_mcp.espn_client import ESPNClient
from espn_fantasy_mcp.config import Config


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
