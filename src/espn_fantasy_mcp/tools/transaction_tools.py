"""Transaction management MCP tools."""

import json
from espn_fantasy_mcp.espn_client import ESPNClient
from espn_fantasy_mcp.config import Config


async def handle_get_pending_transactions(arguments: dict) -> str:
    """Handle get_pending_transactions tool call."""
    league_id = arguments.get("league_id") or Config.get_default_league_id()
    team_id = arguments.get("team_id")
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

        result = client.get_pending_transactions(team_id=team_id)

        team_name = None
        if team_id is not None:
            team = client.get_team(team_id)
            team_name = team.team_name

        pending_waivers = result["pending_waivers"]
        pending_trades = result["pending_trades"]

        response = {
            "success": True,
            "team_id": team_id,
            "team_name": team_name,
            "pending_waiver_count": len(pending_waivers),
            "pending_trade_count": len(pending_trades),
            "pending_waivers": pending_waivers,
            "pending_trades": pending_trades,
        }
        return json.dumps(response, indent=2)

    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "error": type(e).__name__,
                "message": f"Failed to get pending transactions: {e}",
            },
            indent=2,
        )


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
        if hasattr(e, "response") and hasattr(e.response, "json"):
            try:
                error_data = e.response.json()
                if "messages" in error_data:
                    error_msg = "; ".join(error_data["messages"])
            except Exception:
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
        if hasattr(e, "response") and hasattr(e.response, "json"):
            try:
                error_data = e.response.json()
                if "messages" in error_data:
                    error_msg = "; ".join(error_data["messages"])
            except Exception:
                pass

        response = {
            "success": False,
            "error": type(e).__name__,
            "message": f"Failed to drop player: {error_msg}",
        }
        return json.dumps(response, indent=2)


async def handle_claim_waiver(arguments: dict) -> str:
    """Handle claim_waiver tool call."""
    league_id = arguments.get("league_id") or Config.get_default_league_id()
    team_id = arguments.get("team_id")
    add_player_id = arguments.get("add_player_id")
    drop_player_id = arguments.get("drop_player_id")
    bid_amount = arguments.get("bid_amount")
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
            "type": "WAIVER",
            "bid_amount": bid_amount if bid_amount is not None else 0,
            "add": {
                "player_id": add_player_id,
                "player_name": add_player.name,
                "position": add_player.position,
                "pro_team": add_player.team,
                "roster_status": add_player.roster_status,
            },
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
                "message": "Preview of waiver claim. Set confirm=true to execute.",
                "team_id": team_id,
                "team_name": team.team_name,
                "scoring_period_id": scoring_period_id or client.league.currentMatchupPeriod,
                "transaction": transaction_details,
                "note": "Waiver claims are pending until processed during waiver period",
                "instructions": "To execute this waiver claim, call this tool again with confirm=true",
            }
            return json.dumps(response, indent=2)

        # Execute the transaction
        result = client.claim_waiver(
            team_id=team_id,
            add_player_id=add_player_id,
            drop_player_id=drop_player_id,
            bid_amount=bid_amount,
            scoring_period_id=scoring_period_id,
        )

        response = {
            "success": True,
            "executed": True,
            "message": "Waiver claim submitted successfully",
            "transaction_id": result.get("id"),
            "status": result.get("status"),
            "is_pending": result.get("isPending"),
            "bid_amount": result.get("bidAmount"),
            "team_id": team_id,
            "scoring_period_id": result.get("scoringPeriodId"),
            "transaction": transaction_details,
            "note": "Waiver claim is pending and will be processed during the waiver period",
            "raw_response": result,
        }

        return json.dumps(response, indent=2)

    except Exception as e:
        # Handle HTTP errors specially to provide better error messages
        error_msg = str(e)
        if hasattr(e, "response") and hasattr(e.response, "json"):
            try:
                error_data = e.response.json()
                if "messages" in error_data:
                    error_msg = "; ".join(error_data["messages"])
            except Exception:
                pass

        response = {
            "success": False,
            "error": type(e).__name__,
            "message": f"Failed to submit waiver claim: {error_msg}",
        }
        return json.dumps(response, indent=2)


async def handle_cancel_waiver(arguments: dict) -> str:
    """Handle cancel_waiver tool call."""
    league_id = arguments.get("league_id") or Config.get_default_league_id()
    team_id = arguments.get("team_id")
    transaction_id = arguments.get("transaction_id")
    scoring_period_id = arguments.get("scoring_period_id")
    season_year = arguments.get("season_year") or Config.get_default_season_year()
    confirm = arguments.get("confirm", False)

    if not league_id:
        raise ValueError("league_id is required")
    if team_id is None:
        raise ValueError("team_id is required")
    if not transaction_id:
        raise ValueError("transaction_id is required")

    try:
        client = ESPNClient(
            league_id=league_id,
            season_year=season_year,
            espn_s2=Config.ESPN_S2,
            swid=Config.ESPN_SWID,
        )

        # If not confirming, return preview
        if not confirm:
            team = client.get_team(team_id)
            response = {
                "success": True,
                "preview": True,
                "message": "Preview of waiver claim cancellation. Set confirm=true to execute.",
                "team_id": team_id,
                "team_name": team.team_name,
                "transaction_id": transaction_id,
                "scoring_period_id": scoring_period_id or client.league.currentMatchupPeriod,
                "instructions": "To cancel this waiver claim, call this tool again with confirm=true",
            }
            return json.dumps(response, indent=2)

        # Execute the cancellation
        result = client.cancel_waiver(
            team_id=team_id,
            transaction_id=transaction_id,
            scoring_period_id=scoring_period_id,
        )

        response = {
            "success": True,
            "executed": True,
            "message": "Waiver claim cancelled successfully",
            "transaction_id": result.get("id"),
            "status": result.get("status"),
            "related_transaction_id": result.get("relatedTransactionId"),
            "team_id": team_id,
            "scoring_period_id": result.get("scoringPeriodId"),
            "raw_response": result,
        }

        return json.dumps(response, indent=2)

    except Exception as e:
        # Handle HTTP errors specially to provide better error messages
        error_msg = str(e)
        if hasattr(e, "response") and hasattr(e.response, "json"):
            try:
                error_data = e.response.json()
                if "messages" in error_data:
                    error_msg = "; ".join(error_data["messages"])
            except Exception:
                pass

        response = {
            "success": False,
            "error": type(e).__name__,
            "message": f"Failed to cancel waiver claim: {error_msg}",
        }
        return json.dumps(response, indent=2)


async def handle_propose_trade(arguments: dict) -> str:
    """Handle propose_trade tool call."""
    league_id = arguments.get("league_id") or Config.get_default_league_id()
    team_id = arguments.get("team_id")
    receiving_team_id = arguments.get("receiving_team_id")
    send_player_ids = arguments.get("send_player_ids", [])
    receive_player_ids = arguments.get("receive_player_ids", [])
    comment = arguments.get("comment")
    expiration_days = arguments.get("expiration_days", 7)
    scoring_period_id = arguments.get("scoring_period_id")
    season_year = arguments.get("season_year") or Config.get_default_season_year()
    confirm = arguments.get("confirm", False)

    if not league_id:
        raise ValueError("league_id is required")
    if team_id is None:
        raise ValueError("team_id is required")
    if receiving_team_id is None:
        raise ValueError("receiving_team_id is required")
    if not send_player_ids:
        raise ValueError("send_player_ids is required and must not be empty")
    if not receive_player_ids:
        raise ValueError("receive_player_ids is required and must not be empty")

    try:
        client = ESPNClient(
            league_id=league_id,
            season_year=season_year,
            espn_s2=Config.ESPN_S2,
            swid=Config.ESPN_SWID,
        )

        # Validate send players are on proposing team's roster
        proposing_roster = client.get_roster(team_id)
        proposing_roster_map = {p.player_id: p for p in proposing_roster}
        for pid in send_player_ids:
            if pid not in proposing_roster_map:
                return json.dumps(
                    {
                        "success": False,
                        "error": "ValidationError",
                        "message": f"Player ID {pid} is not on your roster (team {team_id})",
                    },
                    indent=2,
                )

        # Validate receive players are on receiving team's roster
        receiving_roster = client.get_roster(receiving_team_id)
        receiving_roster_map = {p.player_id: p for p in receiving_roster}
        for pid in receive_player_ids:
            if pid not in receiving_roster_map:
                return json.dumps(
                    {
                        "success": False,
                        "error": "ValidationError",
                        "message": f"Player ID {pid} is not on the receiving team's roster (team {receiving_team_id})",
                    },
                    indent=2,
                )

        # Build trade details for preview/response
        proposing_team = client.get_team(team_id)
        receiving_team = client.get_team(receiving_team_id)

        trade_details = {
            "sending": [
                {
                    "player_id": pid,
                    "player_name": proposing_roster_map[pid].name,
                    "position": proposing_roster_map[pid].position,
                    "pro_team": proposing_roster_map[pid].team,
                }
                for pid in send_player_ids
            ],
            "receiving": [
                {
                    "player_id": pid,
                    "player_name": receiving_roster_map[pid].name,
                    "position": receiving_roster_map[pid].position,
                    "pro_team": receiving_roster_map[pid].team,
                }
                for pid in receive_player_ids
            ],
        }

        if not confirm:
            response = {
                "success": True,
                "preview": True,
                "message": "Preview of trade proposal. Set confirm=true to send.",
                "from_team": {"team_id": team_id, "team_name": proposing_team.team_name},
                "to_team": {"team_id": receiving_team_id, "team_name": receiving_team.team_name},
                "trade": trade_details,
                "comment": comment,
                "expiration_days": expiration_days,
                "instructions": "To send this trade proposal, call this tool again with confirm=true",
            }
            return json.dumps(response, indent=2)

        result = client.propose_trade(
            team_id=team_id,
            receiving_team_id=receiving_team_id,
            send_player_ids=send_player_ids,
            receive_player_ids=receive_player_ids,
            expiration_days=expiration_days,
            comment=comment,
            scoring_period_id=scoring_period_id,
        )

        response = {
            "success": True,
            "executed": True,
            "message": "Trade proposal sent successfully",
            "transaction_id": result.get("id"),
            "status": result.get("status"),
            "is_pending": result.get("isPending"),
            "from_team": {"team_id": team_id, "team_name": proposing_team.team_name},
            "to_team": {"team_id": receiving_team_id, "team_name": receiving_team.team_name},
            "trade": trade_details,
            "comment": result.get("comment"),
            "note": "Trade proposal is pending. The other team must accept before it is executed.",
            "raw_response": result,
        }
        return json.dumps(response, indent=2)

    except Exception as e:
        error_msg = str(e)
        if hasattr(e, "response") and hasattr(e.response, "json"):
            try:
                error_data = e.response.json()
                if "messages" in error_data:
                    error_msg = "; ".join(error_data["messages"])
            except Exception:
                pass

        return json.dumps(
            {
                "success": False,
                "error": type(e).__name__,
                "message": f"Failed to propose trade: {error_msg}",
            },
            indent=2,
        )


async def handle_cancel_trade(arguments: dict) -> str:
    """Handle cancel_trade tool call."""
    league_id = arguments.get("league_id") or Config.get_default_league_id()
    team_id = arguments.get("team_id")
    transaction_id = arguments.get("transaction_id")
    scoring_period_id = arguments.get("scoring_period_id")
    season_year = arguments.get("season_year") or Config.get_default_season_year()
    confirm = arguments.get("confirm", False)

    if not league_id:
        raise ValueError("league_id is required")
    if team_id is None:
        raise ValueError("team_id is required")
    if not transaction_id:
        raise ValueError("transaction_id is required")

    try:
        client = ESPNClient(
            league_id=league_id,
            season_year=season_year,
            espn_s2=Config.ESPN_S2,
            swid=Config.ESPN_SWID,
        )

        if not confirm:
            team = client.get_team(team_id)
            pending = client.get_pending_transactions(team_id=team_id)
            trade_details = next(
                (t for t in pending["pending_trades"] if t["transaction_id"] == transaction_id),
                None,
            )
            response = {
                "success": True,
                "preview": True,
                "message": "Preview of trade proposal cancellation. Set confirm=true to cancel.",
                "team_id": team_id,
                "team_name": team.team_name,
                "transaction_id": transaction_id,
                "trade": trade_details,
                "instructions": "To cancel this trade proposal, call this tool again with confirm=true",
            }
            return json.dumps(response, indent=2)

        result = client.cancel_trade(
            team_id=team_id,
            transaction_id=transaction_id,
            scoring_period_id=scoring_period_id,
        )

        response = {
            "success": True,
            "executed": True,
            "message": "Trade proposal cancelled successfully",
            "transaction_id": result.get("id"),
            "status": result.get("status"),
            "related_transaction_id": result.get("relatedTransactionId"),
            "raw_response": result,
        }
        return json.dumps(response, indent=2)

    except Exception as e:
        error_msg = str(e)
        if hasattr(e, "response") and hasattr(e.response, "json"):
            try:
                error_data = e.response.json()
                if "messages" in error_data:
                    error_msg = "; ".join(error_data["messages"])
            except Exception:
                pass

        return json.dumps(
            {
                "success": False,
                "error": type(e).__name__,
                "message": f"Failed to cancel trade: {error_msg}",
            },
            indent=2,
        )


async def handle_accept_trade(arguments: dict) -> str:
    """Handle accept_trade tool call."""
    league_id = arguments.get("league_id") or Config.get_default_league_id()
    team_id = arguments.get("team_id")
    transaction_id = arguments.get("transaction_id")
    scoring_period_id = arguments.get("scoring_period_id")
    season_year = arguments.get("season_year") or Config.get_default_season_year()
    confirm = arguments.get("confirm", False)

    if not league_id:
        raise ValueError("league_id is required")
    if team_id is None:
        raise ValueError("team_id is required")
    if not transaction_id:
        raise ValueError("transaction_id is required")

    try:
        client = ESPNClient(
            league_id=league_id,
            season_year=season_year,
            espn_s2=Config.ESPN_S2,
            swid=Config.ESPN_SWID,
        )

        if not confirm:
            team = client.get_team(team_id)
            pending = client.get_pending_transactions(team_id=team_id)
            trade_details = next(
                (t for t in pending["pending_trades"] if t["transaction_id"] == transaction_id),
                None,
            )
            response = {
                "success": True,
                "preview": True,
                "message": "Preview of trade acceptance. Set confirm=true to accept.",
                "team_id": team_id,
                "team_name": team.team_name,
                "transaction_id": transaction_id,
                "trade": trade_details,
                "instructions": "To accept this trade, call this tool again with confirm=true",
            }
            return json.dumps(response, indent=2)

        result = client.accept_trade(
            team_id=team_id,
            transaction_id=transaction_id,
            scoring_period_id=scoring_period_id,
        )

        response = {
            "success": True,
            "executed": True,
            "message": "Trade accepted successfully",
            "transaction_id": result.get("id"),
            "status": result.get("status"),
            "related_transaction_id": result.get("relatedTransactionId"),
            "raw_response": result,
        }
        return json.dumps(response, indent=2)

    except Exception as e:
        error_msg = str(e)
        if hasattr(e, "response") and hasattr(e.response, "json"):
            try:
                error_data = e.response.json()
                if "messages" in error_data:
                    error_msg = "; ".join(error_data["messages"])
            except Exception:
                pass

        return json.dumps(
            {
                "success": False,
                "error": type(e).__name__,
                "message": f"Failed to accept trade: {error_msg}",
            },
            indent=2,
        )


async def handle_decline_trade(arguments: dict) -> str:
    """Handle decline_trade tool call."""
    league_id = arguments.get("league_id") or Config.get_default_league_id()
    team_id = arguments.get("team_id")
    transaction_id = arguments.get("transaction_id")
    comment = arguments.get("comment")
    scoring_period_id = arguments.get("scoring_period_id")
    season_year = arguments.get("season_year") or Config.get_default_season_year()
    confirm = arguments.get("confirm", False)

    if not league_id:
        raise ValueError("league_id is required")
    if team_id is None:
        raise ValueError("team_id is required")
    if not transaction_id:
        raise ValueError("transaction_id is required")

    try:
        client = ESPNClient(
            league_id=league_id,
            season_year=season_year,
            espn_s2=Config.ESPN_S2,
            swid=Config.ESPN_SWID,
        )

        if not confirm:
            team = client.get_team(team_id)
            pending = client.get_pending_transactions(team_id=team_id)
            trade_details = next(
                (t for t in pending["pending_trades"] if t["transaction_id"] == transaction_id),
                None,
            )
            response = {
                "success": True,
                "preview": True,
                "message": "Preview of trade decline. Set confirm=true to decline.",
                "team_id": team_id,
                "team_name": team.team_name,
                "transaction_id": transaction_id,
                "trade": trade_details,
                "comment": comment,
                "instructions": "To decline this trade, call this tool again with confirm=true",
            }
            return json.dumps(response, indent=2)

        result = client.decline_trade(
            team_id=team_id,
            transaction_id=transaction_id,
            comment=comment,
            scoring_period_id=scoring_period_id,
        )

        response = {
            "success": True,
            "executed": True,
            "message": "Trade declined successfully",
            "transaction_id": result.get("id"),
            "status": result.get("status"),
            "related_transaction_id": result.get("relatedTransactionId"),
            "raw_response": result,
        }
        return json.dumps(response, indent=2)

    except Exception as e:
        error_msg = str(e)
        if hasattr(e, "response") and hasattr(e.response, "json"):
            try:
                error_data = e.response.json()
                if "messages" in error_data:
                    error_msg = "; ".join(error_data["messages"])
            except Exception:
                pass

        return json.dumps(
            {
                "success": False,
                "error": type(e).__name__,
                "message": f"Failed to decline trade: {error_msg}",
            },
            indent=2,
        )
