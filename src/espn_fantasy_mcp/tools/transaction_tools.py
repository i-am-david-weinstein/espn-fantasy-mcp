"""Transaction management MCP tools."""
import json
from mcp.types import Tool
from espn_fantasy_mcp.espn_client import ESPNClient
from espn_fantasy_mcp.config import Config


def get_tools() -> list[Tool]:
    """Return transaction management tools."""
    return [
        Tool(
            name="add_free_agent",
            description=(
                "Add a free agent to your team, optionally dropping a player. "
                "Uses a confirmation pattern: first call (confirm=false) previews the changes, "
                "second call (confirm=true) executes them. "
                "If your roster is full, you must specify a player to drop."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "league_id": {
                        "type": "string",
                        "description": "ESPN League ID (defaults to configured league)",
                    },
                    "team_id": {
                        "type": "integer",
                        "description": "Team ID (0-based index)",
                    },
                    "add_player_id": {
                        "type": "integer",
                        "description": "ESPN player ID to add",
                    },
                    "drop_player_id": {
                        "type": "integer",
                        "description": "ESPN player ID to drop (required if roster is full)",
                    },
                    "scoring_period_id": {
                        "type": "integer",
                        "description": "Scoring period (week) for transaction (defaults to current period)",
                    },
                    "season_year": {
                        "type": "integer",
                        "description": "Season year (defaults to current year)",
                    },
                    "confirm": {
                        "type": "boolean",
                        "description": (
                            "If false (default), returns a preview of transaction. "
                            "If true, executes the add/drop transaction."
                        ),
                        "default": False,
                    },
                },
                "required": ["team_id", "add_player_id"],
            },
        ),
        Tool(
            name="drop_player",
            description=(
                "Drop a player from your team. "
                "Uses a confirmation pattern: first call (confirm=false) previews the changes, "
                "second call (confirm=true) executes them."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "league_id": {
                        "type": "string",
                        "description": "ESPN League ID (defaults to configured league)",
                    },
                    "team_id": {
                        "type": "integer",
                        "description": "Team ID (0-based index)",
                    },
                    "player_id": {
                        "type": "integer",
                        "description": "ESPN player ID to drop",
                    },
                    "scoring_period_id": {
                        "type": "integer",
                        "description": "Scoring period (week) for transaction (defaults to current period)",
                    },
                    "season_year": {
                        "type": "integer",
                        "description": "Season year (defaults to current year)",
                    },
                    "confirm": {
                        "type": "boolean",
                        "description": (
                            "If false (default), returns a preview of transaction. "
                            "If true, executes the drop transaction."
                        ),
                        "default": False,
                    },
                },
                "required": ["team_id", "player_id"],
            },
        ),
    ]


async def handle_tool(name: str, arguments: dict) -> str:
    """Handle transaction tool calls."""
    if name == "add_free_agent":
        return await handle_add_free_agent(arguments)
    elif name == "drop_player":
        return await handle_drop_player(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def handle_add_free_agent(arguments: dict) -> str:
    """Handle add_free_agent tool call."""
    league_id = arguments.get("league_id") or Config.get_default_league_id()
    team_id = arguments.get("team_id")
    add_player_id = arguments.get("add_player_id")
    drop_player_id = arguments.get("drop_player_id")
    scoring_period_id = arguments.get("scoring_period_id")
    season_year = arguments.get("season_year") or Config.get_default_season_year()
    confirm = arguments.get("confirm", False)

    if not league_id:
        raise ValueError("league_id is required")
    if team_id is None:
        raise ValueError("team_id is required")
    if add_player_id is None:
        raise ValueError("add_player_id is required")

    try:
        client = ESPNClient(
            league_id=league_id,
            season_year=season_year,
            espn_s2=Config.ESPN_S2,
            swid=Config.ESPN_SWID,
        )

        # Get player information
        add_player = client._find_player_by_id(add_player_id)
        if not add_player:
            response = {
                "success": False,
                "error": "PlayerNotFound",
                "message": f"Player ID {add_player_id} not found",
            }
            return json.dumps(response, indent=2)

        drop_player = None
        if drop_player_id is not None:
            # Validate drop player is on roster
            roster = client.get_roster(team_id)
            roster_map = {player.player_id: player for player in roster}

            if drop_player_id not in roster_map:
                response = {
                    "success": False,
                    "error": "ValidationError",
                    "message": f"Player ID {drop_player_id} not found on team roster",
                }
                return json.dumps(response, indent=2)

            drop_player = roster_map[drop_player_id]

        # Build transaction details
        transaction_details = {
            "add": {
                "player_id": add_player_id,
                "player_name": add_player.name,
                "position": add_player.position,
                "pro_team": add_player.team,
            }
        }

        if drop_player:
            transaction_details["drop"] = {
                "player_id": drop_player_id,
                "player_name": drop_player.name,
                "position": drop_player.position,
                "pro_team": drop_player.team,
            }

        # If not confirming, return preview
        if not confirm:
            team = client.get_team(team_id)
            response = {
                "success": True,
                "preview": True,
                "message": "Preview of add/drop transaction. Set confirm=true to execute.",
                "team_id": team_id,
                "team_name": team.team_name,
                "scoring_period_id": scoring_period_id or client.league.currentMatchupPeriod,
                "transaction": transaction_details,
                "instructions": "To execute this transaction, call this tool again with confirm=true",
            }
            return json.dumps(response, indent=2)

        # Execute the transaction
        result = client.add_free_agent(
            team_id=team_id,
            add_player_id=add_player_id,
            drop_player_id=drop_player_id,
            scoring_period_id=scoring_period_id,
        )

        response = {
            "success": True,
            "executed": True,
            "message": "Add/drop transaction executed successfully",
            "transaction_id": result.get("id"),
            "status": result.get("status"),
            "team_id": team_id,
            "scoring_period_id": result.get("scoringPeriodId"),
            "transaction": transaction_details,
            "raw_response": result,
        }

        return json.dumps(response, indent=2)

    except Exception as e:
        # Handle HTTP errors specially to provide better error messages
        error_msg = str(e)
        if hasattr(e, 'response') and hasattr(e.response, 'json'):
            try:
                error_data = e.response.json()
                if 'messages' in error_data:
                    error_msg = '; '.join(error_data['messages'])
            except:
                pass

        response = {
            "success": False,
            "error": type(e).__name__,
            "message": f"Failed to add free agent: {error_msg}",
        }
        return json.dumps(response, indent=2)


async def handle_drop_player(arguments: dict) -> str:
    """Handle drop_player tool call."""
    league_id = arguments.get("league_id") or Config.get_default_league_id()
    team_id = arguments.get("team_id")
    player_id = arguments.get("player_id")
    scoring_period_id = arguments.get("scoring_period_id")
    season_year = arguments.get("season_year") or Config.get_default_season_year()
    confirm = arguments.get("confirm", False)

    if not league_id:
        raise ValueError("league_id is required")
    if team_id is None:
        raise ValueError("team_id is required")
    if player_id is None:
        raise ValueError("player_id is required")

    try:
        client = ESPNClient(
            league_id=league_id,
            season_year=season_year,
            espn_s2=Config.ESPN_S2,
            swid=Config.ESPN_SWID,
        )

        # Validate player is on roster
        roster = client.get_roster(team_id)
        roster_map = {p.player_id: p for p in roster}

        if player_id not in roster_map:
            response = {
                "success": False,
                "error": "ValidationError",
                "message": f"Player ID {player_id} not found on team roster",
            }
            return json.dumps(response, indent=2)

        player = roster_map[player_id]

        # Build transaction details
        transaction_details = {
            "drop": {
                "player_id": player_id,
                "player_name": player.name,
                "position": player.position,
                "pro_team": player.team,
            }
        }

        # If not confirming, return preview
        if not confirm:
            team = client.get_team(team_id)
            response = {
                "success": True,
                "preview": True,
                "message": "Preview of drop transaction. Set confirm=true to execute.",
                "team_id": team_id,
                "team_name": team.team_name,
                "scoring_period_id": scoring_period_id or client.league.currentMatchupPeriod,
                "transaction": transaction_details,
                "instructions": "To execute this transaction, call this tool again with confirm=true",
            }
            return json.dumps(response, indent=2)

        # Execute the transaction
        result = client.drop_player(
            team_id=team_id,
            player_id=player_id,
            scoring_period_id=scoring_period_id,
        )

        response = {
            "success": True,
            "executed": True,
            "message": "Drop transaction executed successfully",
            "transaction_id": result.get("id"),
            "status": result.get("status"),
            "team_id": team_id,
            "scoring_period_id": result.get("scoringPeriodId"),
            "transaction": transaction_details,
            "raw_response": result,
        }

        return json.dumps(response, indent=2)

    except Exception as e:
        # Handle HTTP errors specially to provide better error messages
        error_msg = str(e)
        if hasattr(e, 'response') and hasattr(e.response, 'json'):
            try:
                error_data = e.response.json()
                if 'messages' in error_data:
                    error_msg = '; '.join(error_data['messages'])
            except:
                pass

        response = {
            "success": False,
            "error": type(e).__name__,
            "message": f"Failed to drop player: {error_msg}",
        }
        return json.dumps(response, indent=2)
