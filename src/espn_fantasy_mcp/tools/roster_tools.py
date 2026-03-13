"""Roster management MCP tools."""

import json
from espn_api.baseball.constant import POSITION_MAP
from espn_fantasy_mcp.espn_client import ESPNClient
from espn_fantasy_mcp.config import Config


async def handle_modify_lineup(arguments: dict) -> str:
    """Handle modify_lineup tool call."""
    league_id = arguments.get("league_id") or Config.get_default_league_id()
    team_id = arguments.get("team_id")
    moves = arguments.get("moves", [])
    scoring_period_id = arguments.get("scoring_period_id")
    season_year = arguments.get("season_year") or Config.get_default_season_year()
    confirm = arguments.get("confirm", False)

    if not league_id:
        raise ValueError("league_id is required")
    if team_id is None:
        raise ValueError("team_id is required")
    if not moves:
        raise ValueError("moves array is required and cannot be empty")

    try:
        client = ESPNClient(
            league_id=league_id,
            season_year=season_year,
            espn_s2=Config.ESPN_S2,
            swid=Config.ESPN_SWID,
        )

        # Get the team's roster to validate moves and provide player names
        roster = client.get_roster(team_id)
        roster_map = {player.player_id: player for player in roster}

        # Validate all moves
        validation_errors = []
        move_details = []

        for idx, move in enumerate(moves):
            player_id = move.get("player_id")
            from_slot = move.get("from_slot")
            to_slot = move.get("to_slot")

            # Validate player is on roster
            if player_id not in roster_map:
                validation_errors.append(
                    f"Move {idx + 1}: Player ID {player_id} not found on team roster"
                )
                continue

            player = roster_map[player_id]

            # Validate from_slot matches current position
            # player.lineup_slot is a string like "P" or "BE", convert from_slot to string for comparison
            current_slot_str = player.lineup_slot
            from_slot_str = POSITION_MAP.get(from_slot, str(from_slot))

            if current_slot_str != from_slot_str:
                validation_errors.append(
                    f"Move {idx + 1}: Player {player.name} is currently in slot {current_slot_str}, not {from_slot_str}"
                )

            move_details.append(
                {
                    "player_id": player_id,
                    "player_name": player.name,
                    "from_slot": from_slot,
                    "from_slot_name": from_slot_str,
                    "to_slot": to_slot,
                    "to_slot_name": POSITION_MAP.get(to_slot, str(to_slot)),
                    "position": player.position,
                }
            )

        if validation_errors:
            response = {
                "success": False,
                "error": "ValidationError",
                "message": "Invalid lineup moves",
                "validation_errors": validation_errors,
            }
            return json.dumps(response, indent=2)

        # If not confirming, return preview
        if not confirm:
            response = {
                "success": True,
                "preview": True,
                "message": "Preview of lineup changes. Set confirm=true to execute.",
                "team_id": team_id,
                "team_name": client.get_team(team_id).team_name,
                "scoring_period_id": scoring_period_id or client.league.currentMatchupPeriod,
                "moves": move_details,
                "instructions": "To execute these changes, call this tool again with confirm=true",
            }
            return json.dumps(response, indent=2)

        # Execute the lineup changes
        result = client.modify_lineup(
            team_id=team_id,
            moves=moves,
            scoring_period_id=scoring_period_id,
        )

        response = {
            "success": True,
            "executed": True,
            "message": "Lineup changes executed successfully",
            "transaction_id": result.get("id"),
            "status": result.get("status"),
            "team_id": team_id,
            "scoring_period_id": result.get("scoringPeriodId"),
            "moves": move_details,
            "raw_response": result,
        }

        return json.dumps(response, indent=2)

    except (ValueError, IndexError, KeyError, AttributeError, ConnectionError) as e:
        response = {
            "success": False,
            "error": type(e).__name__,
            "message": str(e),
        }
        return json.dumps(response, indent=2)
    except Exception as e:
        # Catch any other errors (like HTTP errors from requests)
        response = {
            "success": False,
            "error": type(e).__name__,
            "message": f"Failed to modify lineup: {str(e)}",
        }
        return json.dumps(response, indent=2)
