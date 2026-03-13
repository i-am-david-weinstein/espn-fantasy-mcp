"""Team-related MCP tools."""

import json
from espn_fantasy_mcp.espn_client import ESPNClient
from espn_fantasy_mcp.config import Config


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
