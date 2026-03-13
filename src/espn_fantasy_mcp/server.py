"""MCP server implementation for ESPN Fantasy Baseball."""

import logging
from typing import Optional

from fastmcp import FastMCP

from espn_fantasy_mcp.tools import (
    league_tools,
    team_tools,
    player_tools,
    roster_tools,
    transaction_tools,
)

logger = logging.getLogger(__name__)
mcp = FastMCP("espn-fantasy")


@mcp.tool()
async def get_league_settings(
    league_id: Optional[str] = None,
    season_year: Optional[int] = None,
) -> str:
    """Get league configuration including scoring categories, roster settings, and league rules.

    Args:
        league_id: ESPN League ID (found in league URL)
        season_year: Season year (defaults to current year if not specified)
    """
    return await league_tools.handle_get_league_settings(
        {"league_id": league_id, "season_year": season_year}
    )


@mcp.tool()
async def get_standings(
    league_id: Optional[str] = None,
    season_year: Optional[int] = None,
) -> str:
    """Get current league standings with team records and rankings.

    Args:
        league_id: ESPN League ID
        season_year: Season year (defaults to current year)
    """
    return await league_tools.handle_get_standings(
        {"league_id": league_id, "season_year": season_year}
    )


@mcp.tool()
async def get_team(
    team_id: Optional[int] = None,
    league_id: Optional[str] = None,
    season_year: Optional[int] = None,
) -> str:
    """Get detailed information about a specific team.

    Args:
        team_id: Team ID (1-based index)
        league_id: ESPN League ID
        season_year: Season year (defaults to current year)
    """
    return await team_tools.handle_get_team(
        {"league_id": league_id, "team_id": team_id, "season_year": season_year}
    )


@mcp.tool()
async def get_roster(
    team_id: Optional[int] = None,
    league_id: Optional[str] = None,
    season_year: Optional[int] = None,
) -> str:
    """Get current roster for a team with player details and lineup positions.

    Args:
        team_id: Team ID (1-based index)
        league_id: ESPN League ID
        season_year: Season year (defaults to current year)
    """
    return await team_tools.handle_get_roster(
        {"league_id": league_id, "team_id": team_id, "season_year": season_year}
    )


@mcp.tool()
async def get_free_agents(
    league_id: Optional[str] = None,
    season_year: Optional[int] = None,
    position: Optional[str] = None,
    size: Optional[int] = None,
) -> str:
    """Get list of available free agents on the waiver wire.

    Args:
        league_id: ESPN League ID
        season_year: Season year (defaults to current year)
        position: Filter by position (C, 1B, 2B, SS, 3B, OF, SP, RP, P)
        size: Number of players to return (default: 50)
    """
    return await player_tools.handle_get_free_agents(
        {"league_id": league_id, "season_year": season_year, "position": position, "size": size}
    )


@mcp.tool()
async def get_player_info(
    player_name: str,
    league_id: Optional[str] = None,
    season_year: Optional[int] = None,
) -> str:
    """Look up a player by name and get detailed information including stats, position, team, and roster status. Supports fuzzy matching for misspelled names.

    Args:
        player_name: Player's full name (e.g., 'Shohei Ohtani', 'Aaron Judge')
        league_id: ESPN League ID
        season_year: Season year (defaults to current year)
    """
    return await player_tools.handle_get_player_info(
        {"player_name": player_name, "league_id": league_id, "season_year": season_year}
    )


@mcp.tool()
async def modify_lineup(
    team_id: Optional[int] = None,
    moves: Optional[list[dict]] = None,
    league_id: Optional[str] = None,
    scoring_period_id: Optional[int] = None,
    season_year: Optional[int] = None,
    confirm: bool = False,
) -> str:
    """Modify team lineup by moving players between lineup slots. Uses a confirmation pattern: first call (confirm=false) previews the changes, second call (confirm=true) executes them. Can move a single player or swap multiple players in one transaction.

    Args:
        team_id: Team ID (1-based index)
        moves: List of lineup moves to make, each with player_id, from_slot, and to_slot
        league_id: ESPN League ID (defaults to configured league)
        scoring_period_id: Scoring period (week) for changes (defaults to current period)
        season_year: Season year (defaults to current year)
        confirm: If false (default), returns a preview of changes. If true, executes the lineup changes.
    """
    return await roster_tools.handle_modify_lineup(
        {
            "league_id": league_id,
            "team_id": team_id,
            "moves": moves or [],
            "scoring_period_id": scoring_period_id,
            "season_year": season_year,
            "confirm": confirm,
        }
    )


@mcp.tool()
async def get_pending_transactions(
    league_id: Optional[str] = None,
    team_id: Optional[int] = None,
    season_year: Optional[int] = None,
) -> str:
    """Get waiver claims and trade proposals for a team, including all statuses (PENDING, EXECUTED, CANCELED). Each entry includes its status field. For trades, returns both sent and received proposals.

    Args:
        league_id: ESPN League ID (defaults to configured league)
        team_id: Team ID (1-based index). If omitted, returns all pending transactions league-wide.
        season_year: Season year (defaults to current year)
    """
    return await transaction_tools.handle_get_pending_transactions(
        {"league_id": league_id, "team_id": team_id, "season_year": season_year}
    )


@mcp.tool()
async def add_free_agent(
    team_id: Optional[int] = None,
    add_player_id: Optional[int] = None,
    drop_player_id: Optional[int] = None,
    league_id: Optional[str] = None,
    scoring_period_id: Optional[int] = None,
    season_year: Optional[int] = None,
    confirm: bool = False,
) -> str:
    """Add a free agent to your team, optionally dropping a player. Uses a confirmation pattern: first call (confirm=false) previews the changes, second call (confirm=true) executes them. If your roster is full, you must specify a player to drop.

    Args:
        team_id: Team ID (1-based index)
        add_player_id: ESPN player ID to add
        drop_player_id: ESPN player ID to drop (required if roster is full)
        league_id: ESPN League ID (defaults to configured league)
        scoring_period_id: Scoring period (week) for transaction (defaults to current period)
        season_year: Season year (defaults to current year)
        confirm: If false (default), returns a preview of transaction. If true, executes the add/drop transaction.
    """
    return await transaction_tools.handle_add_free_agent(
        {
            "league_id": league_id,
            "team_id": team_id,
            "add_player_id": add_player_id,
            "drop_player_id": drop_player_id,
            "scoring_period_id": scoring_period_id,
            "season_year": season_year,
            "confirm": confirm,
        }
    )


@mcp.tool()
async def drop_player(
    team_id: Optional[int] = None,
    player_id: Optional[int] = None,
    league_id: Optional[str] = None,
    scoring_period_id: Optional[int] = None,
    season_year: Optional[int] = None,
    confirm: bool = False,
) -> str:
    """Drop a player from your team. Uses a confirmation pattern: first call (confirm=false) previews the changes, second call (confirm=true) executes them.

    Args:
        team_id: Team ID (1-based index)
        player_id: ESPN player ID to drop
        league_id: ESPN League ID (defaults to configured league)
        scoring_period_id: Scoring period (week) for transaction (defaults to current period)
        season_year: Season year (defaults to current year)
        confirm: If false (default), returns a preview of transaction. If true, executes the drop transaction.
    """
    return await transaction_tools.handle_drop_player(
        {
            "league_id": league_id,
            "team_id": team_id,
            "player_id": player_id,
            "scoring_period_id": scoring_period_id,
            "season_year": season_year,
            "confirm": confirm,
        }
    )


@mcp.tool()
async def claim_waiver(
    team_id: Optional[int] = None,
    add_player_id: Optional[int] = None,
    drop_player_id: Optional[int] = None,
    bid_amount: Optional[int] = None,
    league_id: Optional[str] = None,
    scoring_period_id: Optional[int] = None,
    season_year: Optional[int] = None,
    confirm: bool = False,
) -> str:
    """Submit a waiver claim with optional FAAB bid. Uses a confirmation pattern: first call (confirm=false) previews the changes, second call (confirm=true) executes them. Waiver claims are processed during waiver periods and have a pending status until processed. If your roster is full, you must specify a player to drop.

    Args:
        team_id: Team ID (1-based index)
        add_player_id: ESPN player ID to claim off waivers
        drop_player_id: ESPN player ID to drop (required if roster is full)
        bid_amount: FAAB bid amount (defaults to 0 for free waiver claim)
        league_id: ESPN League ID (defaults to configured league)
        scoring_period_id: Scoring period (week) for transaction (defaults to current period)
        season_year: Season year (defaults to current year)
        confirm: If false (default), returns a preview of waiver claim. If true, executes the waiver claim.
    """
    return await transaction_tools.handle_claim_waiver(
        {
            "league_id": league_id,
            "team_id": team_id,
            "add_player_id": add_player_id,
            "drop_player_id": drop_player_id,
            "bid_amount": bid_amount,
            "scoring_period_id": scoring_period_id,
            "season_year": season_year,
            "confirm": confirm,
        }
    )


@mcp.tool()
async def cancel_waiver(
    team_id: Optional[int] = None,
    transaction_id: Optional[str] = None,
    league_id: Optional[str] = None,
    scoring_period_id: Optional[int] = None,
    season_year: Optional[int] = None,
    confirm: bool = False,
) -> str:
    """Cancel a pending waiver claim. Uses a confirmation pattern: first call (confirm=false) previews the cancellation, second call (confirm=true) executes it. You need the transaction ID from the original waiver claim to cancel it.

    Args:
        team_id: Team ID (1-based index)
        transaction_id: Transaction ID from the original waiver claim response
        league_id: ESPN League ID (defaults to configured league)
        scoring_period_id: Scoring period (week) for transaction (defaults to current period)
        season_year: Season year (defaults to current year)
        confirm: If false (default), returns a preview of cancellation. If true, executes the waiver claim cancellation.
    """
    return await transaction_tools.handle_cancel_waiver(
        {
            "league_id": league_id,
            "team_id": team_id,
            "transaction_id": transaction_id,
            "scoring_period_id": scoring_period_id,
            "season_year": season_year,
            "confirm": confirm,
        }
    )


@mcp.tool()
async def propose_trade(
    team_id: Optional[int] = None,
    receiving_team_id: Optional[int] = None,
    send_player_ids: Optional[list[int]] = None,
    receive_player_ids: Optional[list[int]] = None,
    comment: Optional[str] = None,
    expiration_days: Optional[int] = None,
    league_id: Optional[str] = None,
    scoring_period_id: Optional[int] = None,
    season_year: Optional[int] = None,
    confirm: bool = False,
) -> str:
    """Propose a trade with another team. Uses a confirmation pattern: first call (confirm=false) previews the trade, second call (confirm=true) sends it. Returns a transaction ID that can be used to cancel the proposal.

    Args:
        team_id: Your team ID (1-based index)
        receiving_team_id: The other team's ID (1-based index)
        send_player_ids: ESPN player IDs you are sending to the other team
        receive_player_ids: ESPN player IDs you want to receive from the other team
        comment: Optional message to include with the trade offer
        expiration_days: Days until the trade offer expires (default: 7)
        league_id: ESPN League ID (defaults to configured league)
        scoring_period_id: Scoring period for the transaction (defaults to current)
        season_year: Season year (defaults to current year)
        confirm: If false (default), returns a preview of the trade. If true, sends the trade proposal.
    """
    return await transaction_tools.handle_propose_trade(
        {
            "league_id": league_id,
            "team_id": team_id,
            "receiving_team_id": receiving_team_id,
            "send_player_ids": send_player_ids or [],
            "receive_player_ids": receive_player_ids or [],
            "comment": comment,
            "expiration_days": expiration_days,
            "scoring_period_id": scoring_period_id,
            "season_year": season_year,
            "confirm": confirm,
        }
    )


@mcp.tool()
async def cancel_trade(
    team_id: Optional[int] = None,
    transaction_id: Optional[str] = None,
    league_id: Optional[str] = None,
    scoring_period_id: Optional[int] = None,
    season_year: Optional[int] = None,
    confirm: bool = False,
) -> str:
    """Cancel a pending trade proposal you sent. Uses a confirmation pattern: first call (confirm=false) previews the cancellation, second call (confirm=true) executes it. You need the transaction ID from the original trade proposal.

    Args:
        team_id: Your team ID (1-based index)
        transaction_id: Transaction ID from the original trade proposal
        league_id: ESPN League ID (defaults to configured league)
        scoring_period_id: Scoring period for the transaction (defaults to current)
        season_year: Season year (defaults to current year)
        confirm: If false (default), returns a preview. If true, cancels the trade proposal.
    """
    return await transaction_tools.handle_cancel_trade(
        {
            "league_id": league_id,
            "team_id": team_id,
            "transaction_id": transaction_id,
            "scoring_period_id": scoring_period_id,
            "season_year": season_year,
            "confirm": confirm,
        }
    )


@mcp.tool()
async def accept_trade(
    team_id: Optional[int] = None,
    transaction_id: Optional[str] = None,
    league_id: Optional[str] = None,
    scoring_period_id: Optional[int] = None,
    season_year: Optional[int] = None,
    confirm: bool = False,
) -> str:
    """Accept a pending trade offer from another team. Uses a confirmation pattern: first call (confirm=false) previews the acceptance, second call (confirm=true) executes it. You need the transaction ID from the trade proposal.

    Args:
        team_id: Your team ID (1-based index)
        transaction_id: Transaction ID of the trade proposal to accept
        league_id: ESPN League ID (defaults to configured league)
        scoring_period_id: Scoring period for the transaction (defaults to current)
        season_year: Season year (defaults to current year)
        confirm: If false (default), returns a preview. If true, accepts the trade.
    """
    return await transaction_tools.handle_accept_trade(
        {
            "league_id": league_id,
            "team_id": team_id,
            "transaction_id": transaction_id,
            "scoring_period_id": scoring_period_id,
            "season_year": season_year,
            "confirm": confirm,
        }
    )


@mcp.tool()
async def decline_trade(
    team_id: Optional[int] = None,
    transaction_id: Optional[str] = None,
    comment: Optional[str] = None,
    league_id: Optional[str] = None,
    scoring_period_id: Optional[int] = None,
    season_year: Optional[int] = None,
    confirm: bool = False,
) -> str:
    """Decline a trade offer from another team. Uses a confirmation pattern: first call (confirm=false) previews the decline, second call (confirm=true) executes it.

    Args:
        team_id: Your team ID (1-based index)
        transaction_id: Transaction ID of the trade proposal to decline
        comment: Optional reason for declining
        league_id: ESPN League ID (defaults to configured league)
        scoring_period_id: Scoring period for the transaction (defaults to current)
        season_year: Season year (defaults to current year)
        confirm: If false (default), returns a preview. If true, declines the trade.
    """
    return await transaction_tools.handle_decline_trade(
        {
            "league_id": league_id,
            "team_id": team_id,
            "transaction_id": transaction_id,
            "comment": comment,
            "scoring_period_id": scoring_period_id,
            "season_year": season_year,
            "confirm": confirm,
        }
    )


def main():
    """Run the MCP server."""
    logger.info("Starting ESPN Fantasy MCP server")
    mcp.run()
