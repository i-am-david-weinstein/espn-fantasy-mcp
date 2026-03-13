"""Unit tests for trade tools and get_pending_transactions."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from espn_fantasy_mcp.tools import transaction_tools


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_roster_player(
    player_id: int, name: str = "Player", team: str = "NYY", position: str = "OF"
) -> Mock:
    p = Mock()
    p.player_id = player_id
    p.name = name
    p.team = team
    p.position = position
    return p


def _make_espn_client(
    proposing_team_id: int = 1,
    receiving_team_id: int = 2,
    proposing_roster: list | None = None,
    receiving_roster: list | None = None,
) -> Mock:
    """Return a mock ESPNClient pre-configured for trade tests.

    team IDs here are the 1-based indices used by the MCP tool layer,
    matching what handle_propose_trade passes to client.get_roster().
    """
    client = Mock()
    client.league.currentMatchupPeriod = 5

    # get_team returns a different mock depending on which team_id is passed
    def _get_team(tid):
        t = Mock()
        t.team_name = f"Team {tid}"
        return t

    client.get_team.side_effect = _get_team

    if proposing_roster is None:
        proposing_roster = [_make_roster_player(100, "Sender Player")]
    if receiving_roster is None:
        receiving_roster = [_make_roster_player(200, "Receiver Player")]

    def _get_roster(tid):
        if tid == proposing_team_id:
            return proposing_roster
        return receiving_roster

    client.get_roster.side_effect = _get_roster

    client.propose_trade.return_value = {
        "id": "trade-proposal-abc",
        "status": "PENDING",
        "isPending": True,
        "comment": None,
    }
    client.cancel_trade.return_value = {
        "id": "cancel-txn-xyz",
        "status": "CANCELED",
        "relatedTransactionId": "trade-proposal-abc",
    }
    client.accept_trade.return_value = {
        "id": "accept-txn-xyz",
        "status": "EXECUTED",
        "relatedTransactionId": "trade-proposal-abc",
    }
    client.decline_trade.return_value = {
        "id": "decline-txn-xyz",
        "status": "EXECUTED",
        "relatedTransactionId": "trade-proposal-abc",
    }
    client.get_pending_transactions.return_value = {
        "pending_waivers": [],
        "pending_trades": [
            {
                "transaction_id": "trade-proposal-abc",
                "type": "TRADE_PROPOSAL",
                "status": "PENDING",
                "is_pending_vote": False,
                "proposing_team_id": 1,
                "proposing_team_name": "Team 0",
                "items": [
                    {
                        "player_id": 100,
                        "player_name": "Sender Player",
                        "from_team_id": 1,
                        "from_team_name": "Team 0",
                        "to_team_id": 2,
                        "to_team_name": "Team 1",
                    },
                    {
                        "player_id": 200,
                        "player_name": "Receiver Player",
                        "from_team_id": 2,
                        "from_team_name": "Team 1",
                        "to_team_id": 1,
                        "to_team_name": "Team 0",
                    },
                ],
            }
        ],
    }
    return client


# ---------------------------------------------------------------------------
# propose_trade – tool schema
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestProposeTradeToolSchema:
    def test_tool_is_registered(self):
        names = [t.name for t in transaction_tools.get_tools()]
        assert "propose_trade" in names

    def test_required_fields(self):
        tool = next(t for t in transaction_tools.get_tools() if t.name == "propose_trade")
        required = tool.inputSchema["required"]
        assert "team_id" in required
        assert "receiving_team_id" in required
        assert "send_player_ids" in required
        assert "receive_player_ids" in required

    def test_confirm_defaults_to_false(self):
        tool = next(t for t in transaction_tools.get_tools() if t.name == "propose_trade")
        assert tool.inputSchema["properties"]["confirm"]["default"] is False

    def test_send_receive_player_ids_are_arrays(self):
        tool = next(t for t in transaction_tools.get_tools() if t.name == "propose_trade")
        props = tool.inputSchema["properties"]
        assert props["send_player_ids"]["type"] == "array"
        assert props["receive_player_ids"]["type"] == "array"


# ---------------------------------------------------------------------------
# propose_trade – validation
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestProposeTradeValidation:
    @pytest.mark.asyncio
    async def test_missing_league_id_raises(self, monkeypatch):
        import espn_fantasy_mcp.tools.transaction_tools as tt

        monkeypatch.setattr(tt.Config, "ESPN_LEAGUE_ID", None)
        with pytest.raises(ValueError, match="league_id is required"):
            await transaction_tools.handle_propose_trade(
                {
                    "team_id": 1,
                    "receiving_team_id": 2,
                    "send_player_ids": [100],
                    "receive_player_ids": [200],
                }
            )

    @pytest.mark.asyncio
    async def test_missing_send_player_ids_raises(self, mock_env_vars):
        with pytest.raises(ValueError, match="send_player_ids"):
            await transaction_tools.handle_propose_trade(
                {
                    "league_id": "123456",
                    "team_id": 1,
                    "receiving_team_id": 2,
                    "send_player_ids": [],
                    "receive_player_ids": [200],
                }
            )

    @pytest.mark.asyncio
    async def test_missing_receive_player_ids_raises(self, mock_env_vars):
        with pytest.raises(ValueError, match="receive_player_ids"):
            await transaction_tools.handle_propose_trade(
                {
                    "league_id": "123456",
                    "team_id": 1,
                    "receiving_team_id": 2,
                    "send_player_ids": [100],
                    "receive_player_ids": [],
                }
            )

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_send_player_not_on_proposing_roster_fails(
        self, mock_client_class, mock_env_vars
    ):
        client = _make_espn_client(
            proposing_roster=[_make_roster_player(100)],
            receiving_roster=[_make_roster_player(200)],
        )
        mock_client_class.return_value = client

        result = await transaction_tools.handle_propose_trade(
            {
                "league_id": "123456",
                "team_id": 1,
                "receiving_team_id": 2,
                "send_player_ids": [999],  # not on roster
                "receive_player_ids": [200],
            }
        )

        response = json.loads(result)
        assert response["success"] is False
        assert response["error"] == "ValidationError"
        assert "999" in response["message"]

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_receive_player_not_on_receiving_roster_fails(
        self, mock_client_class, mock_env_vars
    ):
        client = _make_espn_client(
            proposing_roster=[_make_roster_player(100)],
            receiving_roster=[_make_roster_player(200)],
        )
        mock_client_class.return_value = client

        result = await transaction_tools.handle_propose_trade(
            {
                "league_id": "123456",
                "team_id": 1,
                "receiving_team_id": 2,
                "send_player_ids": [100],
                "receive_player_ids": [999],  # not on receiving team
            }
        )

        response = json.loads(result)
        assert response["success"] is False
        assert response["error"] == "ValidationError"
        assert "999" in response["message"]


# ---------------------------------------------------------------------------
# propose_trade – preview (confirm=False)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestProposeTradePreview:
    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_preview_returns_success_and_preview_flag(self, mock_client_class, mock_env_vars):
        mock_client_class.return_value = _make_espn_client()
        result = await transaction_tools.handle_propose_trade(
            {
                "league_id": "123456",
                "team_id": 1,
                "receiving_team_id": 2,
                "send_player_ids": [100],
                "receive_player_ids": [200],
            }
        )
        response = json.loads(result)
        assert response["success"] is True
        assert response["preview"] is True

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_preview_does_not_call_propose_trade(self, mock_client_class, mock_env_vars):
        client = _make_espn_client()
        mock_client_class.return_value = client
        await transaction_tools.handle_propose_trade(
            {
                "league_id": "123456",
                "team_id": 1,
                "receiving_team_id": 2,
                "send_player_ids": [100],
                "receive_player_ids": [200],
            }
        )
        client.propose_trade.assert_not_called()

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_preview_includes_player_names(self, mock_client_class, mock_env_vars):
        client = _make_espn_client(
            proposing_roster=[_make_roster_player(100, "Aaron Judge")],
            receiving_roster=[_make_roster_player(200, "Shohei Ohtani")],
        )
        mock_client_class.return_value = client
        result = await transaction_tools.handle_propose_trade(
            {
                "league_id": "123456",
                "team_id": 1,
                "receiving_team_id": 2,
                "send_player_ids": [100],
                "receive_player_ids": [200],
            }
        )
        response = json.loads(result)
        assert response["trade"]["sending"][0]["player_name"] == "Aaron Judge"
        assert response["trade"]["receiving"][0]["player_name"] == "Shohei Ohtani"

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_preview_includes_team_names(self, mock_client_class, mock_env_vars):
        mock_client_class.return_value = _make_espn_client()
        result = await transaction_tools.handle_propose_trade(
            {
                "league_id": "123456",
                "team_id": 1,
                "receiving_team_id": 2,
                "send_player_ids": [100],
                "receive_player_ids": [200],
            }
        )
        response = json.loads(result)
        assert response["from_team"]["team_id"] == 1
        assert response["to_team"]["team_id"] == 2

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_preview_instructions_mention_confirm(self, mock_client_class, mock_env_vars):
        mock_client_class.return_value = _make_espn_client()
        result = await transaction_tools.handle_propose_trade(
            {
                "league_id": "123456",
                "team_id": 1,
                "receiving_team_id": 2,
                "send_player_ids": [100],
                "receive_player_ids": [200],
            }
        )
        response = json.loads(result)
        assert "confirm=true" in response["instructions"]


# ---------------------------------------------------------------------------
# propose_trade – execute (confirm=True)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestProposeTradeExecute:
    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_execute_calls_propose_trade_with_correct_args(
        self, mock_client_class, mock_env_vars
    ):
        client = _make_espn_client()
        mock_client_class.return_value = client

        await transaction_tools.handle_propose_trade(
            {
                "league_id": "123456",
                "team_id": 1,
                "receiving_team_id": 2,
                "send_player_ids": [100],
                "receive_player_ids": [200],
                "comment": "Good deal",
                "expiration_days": 3,
                "scoring_period_id": 7,
                "confirm": True,
            }
        )

        client.propose_trade.assert_called_once_with(
            team_id=1,
            receiving_team_id=2,
            send_player_ids=[100],
            receive_player_ids=[200],
            expiration_days=3,
            comment="Good deal",
            scoring_period_id=7,
        )

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_execute_returns_transaction_id_and_status(
        self, mock_client_class, mock_env_vars
    ):
        mock_client_class.return_value = _make_espn_client()
        result = await transaction_tools.handle_propose_trade(
            {
                "league_id": "123456",
                "team_id": 1,
                "receiving_team_id": 2,
                "send_player_ids": [100],
                "receive_player_ids": [200],
                "confirm": True,
            }
        )
        response = json.loads(result)
        assert response["success"] is True
        assert response["executed"] is True
        assert response["transaction_id"] == "trade-proposal-abc"
        assert response["status"] == "PENDING"
        assert response["is_pending"] is True

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_execute_uses_default_expiration_days(self, mock_client_class, mock_env_vars):
        client = _make_espn_client()
        mock_client_class.return_value = client

        await transaction_tools.handle_propose_trade(
            {
                "league_id": "123456",
                "team_id": 1,
                "receiving_team_id": 2,
                "send_player_ids": [100],
                "receive_player_ids": [200],
                "confirm": True,
            }
        )

        assert client.propose_trade.call_args.kwargs["expiration_days"] == 7


# ---------------------------------------------------------------------------
# cancel_trade – schema, preview, execute
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCancelTradeToolSchema:
    def test_tool_is_registered(self):
        names = [t.name for t in transaction_tools.get_tools()]
        assert "cancel_trade" in names

    def test_required_fields(self):
        tool = next(t for t in transaction_tools.get_tools() if t.name == "cancel_trade")
        assert "team_id" in tool.inputSchema["required"]
        assert "transaction_id" in tool.inputSchema["required"]


@pytest.mark.unit
class TestCancelTradePreview:
    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_preview_returns_success(self, mock_client_class, mock_env_vars):
        mock_client_class.return_value = _make_espn_client()
        result = await transaction_tools.handle_cancel_trade(
            {
                "league_id": "123456",
                "team_id": 2,
                "transaction_id": "trade-proposal-abc",
            }
        )
        response = json.loads(result)
        assert response["success"] is True
        assert response["preview"] is True

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_preview_does_not_cancel(self, mock_client_class, mock_env_vars):
        client = _make_espn_client()
        mock_client_class.return_value = client
        await transaction_tools.handle_cancel_trade(
            {
                "league_id": "123456",
                "team_id": 2,
                "transaction_id": "trade-proposal-abc",
            }
        )
        client.cancel_trade.assert_not_called()

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_preview_includes_transaction_id(self, mock_client_class, mock_env_vars):
        mock_client_class.return_value = _make_espn_client()
        result = await transaction_tools.handle_cancel_trade(
            {
                "league_id": "123456",
                "team_id": 2,
                "transaction_id": "trade-proposal-abc",
            }
        )
        response = json.loads(result)
        assert response["transaction_id"] == "trade-proposal-abc"

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_preview_includes_trade_details(self, mock_client_class, mock_env_vars):
        mock_client_class.return_value = _make_espn_client()
        result = await transaction_tools.handle_cancel_trade(
            {
                "league_id": "123456",
                "team_id": 2,
                "transaction_id": "trade-proposal-abc",
            }
        )
        response = json.loads(result)
        assert response["trade"] is not None
        assert response["trade"]["transaction_id"] == "trade-proposal-abc"
        assert len(response["trade"]["items"]) == 2


@pytest.mark.unit
class TestCancelTradeExecute:
    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_execute_calls_cancel_trade(self, mock_client_class, mock_env_vars):
        client = _make_espn_client()
        mock_client_class.return_value = client
        await transaction_tools.handle_cancel_trade(
            {
                "league_id": "123456",
                "team_id": 2,
                "transaction_id": "trade-proposal-abc",
                "scoring_period_id": 5,
                "confirm": True,
            }
        )
        client.cancel_trade.assert_called_once_with(
            team_id=2,
            transaction_id="trade-proposal-abc",
            scoring_period_id=5,
        )

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_execute_returns_canceled_status(self, mock_client_class, mock_env_vars):
        mock_client_class.return_value = _make_espn_client()
        result = await transaction_tools.handle_cancel_trade(
            {
                "league_id": "123456",
                "team_id": 2,
                "transaction_id": "trade-proposal-abc",
                "confirm": True,
            }
        )
        response = json.loads(result)
        assert response["success"] is True
        assert response["executed"] is True
        assert response["status"] == "CANCELED"
        assert response["related_transaction_id"] == "trade-proposal-abc"


# ---------------------------------------------------------------------------
# accept_trade – schema, preview, execute
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestAcceptTradeToolSchema:
    def test_tool_is_registered(self):
        names = [t.name for t in transaction_tools.get_tools()]
        assert "accept_trade" in names

    def test_required_fields(self):
        tool = next(t for t in transaction_tools.get_tools() if t.name == "accept_trade")
        assert "team_id" in tool.inputSchema["required"]
        assert "transaction_id" in tool.inputSchema["required"]


@pytest.mark.unit
class TestAcceptTradePreview:
    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_preview_returns_success(self, mock_client_class, mock_env_vars):
        mock_client_class.return_value = _make_espn_client()
        result = await transaction_tools.handle_accept_trade(
            {
                "league_id": "123456",
                "team_id": 2,
                "transaction_id": "trade-proposal-abc",
            }
        )
        response = json.loads(result)
        assert response["success"] is True
        assert response["preview"] is True

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_preview_does_not_accept(self, mock_client_class, mock_env_vars):
        client = _make_espn_client()
        mock_client_class.return_value = client
        await transaction_tools.handle_accept_trade(
            {
                "league_id": "123456",
                "team_id": 2,
                "transaction_id": "trade-proposal-abc",
            }
        )
        client.accept_trade.assert_not_called()

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_preview_includes_trade_details(self, mock_client_class, mock_env_vars):
        mock_client_class.return_value = _make_espn_client()
        result = await transaction_tools.handle_accept_trade(
            {
                "league_id": "123456",
                "team_id": 2,
                "transaction_id": "trade-proposal-abc",
            }
        )
        response = json.loads(result)
        assert response["trade"] is not None
        assert response["trade"]["transaction_id"] == "trade-proposal-abc"
        assert len(response["trade"]["items"]) == 2


@pytest.mark.unit
class TestAcceptTradeExecute:
    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_execute_calls_accept_trade(self, mock_client_class, mock_env_vars):
        client = _make_espn_client()
        mock_client_class.return_value = client
        await transaction_tools.handle_accept_trade(
            {
                "league_id": "123456",
                "team_id": 2,
                "transaction_id": "trade-proposal-abc",
                "scoring_period_id": 5,
                "confirm": True,
            }
        )
        client.accept_trade.assert_called_once_with(
            team_id=2,
            transaction_id="trade-proposal-abc",
            scoring_period_id=5,
        )

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_execute_returns_executed_status(self, mock_client_class, mock_env_vars):
        mock_client_class.return_value = _make_espn_client()
        result = await transaction_tools.handle_accept_trade(
            {
                "league_id": "123456",
                "team_id": 2,
                "transaction_id": "trade-proposal-abc",
                "confirm": True,
            }
        )
        response = json.loads(result)
        assert response["success"] is True
        assert response["executed"] is True
        assert response["status"] == "EXECUTED"
        assert response["related_transaction_id"] == "trade-proposal-abc"


# ---------------------------------------------------------------------------
# decline_trade – schema, preview, execute
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDeclineTradeToolSchema:
    def test_tool_is_registered(self):
        names = [t.name for t in transaction_tools.get_tools()]
        assert "decline_trade" in names

    def test_required_fields(self):
        tool = next(t for t in transaction_tools.get_tools() if t.name == "decline_trade")
        assert "team_id" in tool.inputSchema["required"]
        assert "transaction_id" in tool.inputSchema["required"]


@pytest.mark.unit
class TestDeclineTradePreview:
    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_preview_returns_success(self, mock_client_class, mock_env_vars):
        mock_client_class.return_value = _make_espn_client()
        result = await transaction_tools.handle_decline_trade(
            {
                "league_id": "123456",
                "team_id": 2,
                "transaction_id": "trade-proposal-abc",
            }
        )
        response = json.loads(result)
        assert response["success"] is True
        assert response["preview"] is True

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_preview_does_not_decline(self, mock_client_class, mock_env_vars):
        client = _make_espn_client()
        mock_client_class.return_value = client
        await transaction_tools.handle_decline_trade(
            {
                "league_id": "123456",
                "team_id": 2,
                "transaction_id": "trade-proposal-abc",
            }
        )
        client.decline_trade.assert_not_called()

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_preview_includes_comment(self, mock_client_class, mock_env_vars):
        mock_client_class.return_value = _make_espn_client()
        result = await transaction_tools.handle_decline_trade(
            {
                "league_id": "123456",
                "team_id": 2,
                "transaction_id": "trade-proposal-abc",
                "comment": "No thanks",
            }
        )
        response = json.loads(result)
        assert response["comment"] == "No thanks"

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_preview_includes_trade_details(self, mock_client_class, mock_env_vars):
        mock_client_class.return_value = _make_espn_client()
        result = await transaction_tools.handle_decline_trade(
            {
                "league_id": "123456",
                "team_id": 2,
                "transaction_id": "trade-proposal-abc",
            }
        )
        response = json.loads(result)
        assert response["trade"] is not None
        assert response["trade"]["transaction_id"] == "trade-proposal-abc"
        assert len(response["trade"]["items"]) == 2


@pytest.mark.unit
class TestDeclineTradeExecute:
    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_execute_calls_decline_trade_with_comment(self, mock_client_class, mock_env_vars):
        client = _make_espn_client()
        mock_client_class.return_value = client
        await transaction_tools.handle_decline_trade(
            {
                "league_id": "123456",
                "team_id": 2,
                "transaction_id": "trade-proposal-abc",
                "comment": "No thanks",
                "scoring_period_id": 5,
                "confirm": True,
            }
        )
        client.decline_trade.assert_called_once_with(
            team_id=2,
            transaction_id="trade-proposal-abc",
            comment="No thanks",
            scoring_period_id=5,
        )

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_execute_returns_executed_status(self, mock_client_class, mock_env_vars):
        mock_client_class.return_value = _make_espn_client()
        result = await transaction_tools.handle_decline_trade(
            {
                "league_id": "123456",
                "team_id": 2,
                "transaction_id": "trade-proposal-abc",
                "confirm": True,
            }
        )
        response = json.loads(result)
        assert response["success"] is True
        assert response["executed"] is True
        assert response["status"] == "EXECUTED"


# ---------------------------------------------------------------------------
# handle_tool dispatch
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTradeHandleToolDispatch:
    @pytest.mark.asyncio
    async def test_dispatch_propose_trade(self, mock_env_vars):
        with patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient") as mc:
            mc.return_value = _make_espn_client()
            result = await transaction_tools.handle_tool(
                "propose_trade",
                {
                    "league_id": "123456",
                    "team_id": 1,
                    "receiving_team_id": 2,
                    "send_player_ids": [100],
                    "receive_player_ids": [200],
                },
            )
        assert json.loads(result)["success"] is True

    @pytest.mark.asyncio
    async def test_dispatch_cancel_trade(self, mock_env_vars):
        with patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient") as mc:
            mc.return_value = _make_espn_client()
            result = await transaction_tools.handle_tool(
                "cancel_trade",
                {
                    "league_id": "123456",
                    "team_id": 1,
                    "transaction_id": "trade-proposal-abc",
                },
            )
        assert json.loads(result)["success"] is True

    @pytest.mark.asyncio
    async def test_dispatch_accept_trade(self, mock_env_vars):
        with patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient") as mc:
            mc.return_value = _make_espn_client()
            result = await transaction_tools.handle_tool(
                "accept_trade",
                {
                    "league_id": "123456",
                    "team_id": 1,
                    "transaction_id": "trade-proposal-abc",
                },
            )
        assert json.loads(result)["success"] is True

    @pytest.mark.asyncio
    async def test_dispatch_decline_trade(self, mock_env_vars):
        with patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient") as mc:
            mc.return_value = _make_espn_client()
            result = await transaction_tools.handle_tool(
                "decline_trade",
                {
                    "league_id": "123456",
                    "team_id": 1,
                    "transaction_id": "trade-proposal-abc",
                },
            )
        assert json.loads(result)["success"] is True


# ---------------------------------------------------------------------------
# get_pending_transactions – ESPNClient unit tests
# ---------------------------------------------------------------------------


def _make_league_with_transactions(transactions: list) -> Mock:
    """Build a mock league whose espn_request returns the given transactions."""
    team_a = Mock()
    team_a.team_id = 1
    team_a.team_name = "Team A"

    team_b = Mock()
    team_b.team_id = 2
    team_b.team_name = "Team B"

    league = Mock()
    league.currentMatchupPeriod = 5
    league.teams = [team_a, team_b]
    league.player_map = {100: "Sender Player", 200: "Receiver Player"}
    league.espn_request.league_get.return_value = {"transactions": transactions}
    return league


@pytest.mark.unit
class TestGetPendingTransactionsESPNClient:
    """Unit tests for ESPNClient.get_pending_transactions."""

    @patch("espn_fantasy_mcp.espn_client.League")
    def test_returns_empty_when_no_transactions(self, mock_league_class):
        league = _make_league_with_transactions([])
        mock_league_class.return_value = league

        from espn_fantasy_mcp.espn_client import ESPNClient

        client = ESPNClient(league_id="123456", espn_s2="s2", swid="{swid}")
        result = client.get_pending_transactions()

        assert result["pending_waivers"] == []
        assert result["pending_trades"] == []

    @patch("espn_fantasy_mcp.espn_client.League")
    def test_pending_waiver_included(self, mock_league_class):
        txn = {
            "id": "waiver-1",
            "type": "WAIVER",
            "status": "PENDING",
            "teamId": 1,
            "bidAmount": 10,
            "scoringPeriodId": 5,
            "items": [
                {"type": "ADD", "playerId": 200},
                {"type": "DROP", "playerId": 100},
            ],
        }
        league = _make_league_with_transactions([txn])
        mock_league_class.return_value = league

        from espn_fantasy_mcp.espn_client import ESPNClient

        client = ESPNClient(league_id="123456", espn_s2="s2", swid="{swid}")
        result = client.get_pending_transactions()

        assert len(result["pending_waivers"]) == 1
        w = result["pending_waivers"][0]
        assert w["transaction_id"] == "waiver-1"
        assert w["status"] == "PENDING"
        assert w["bid_amount"] == 10
        assert w["add_player"]["player_id"] == 200
        assert w["drop_player"]["player_id"] == 100

    @patch("espn_fantasy_mcp.espn_client.League")
    def test_pending_trade_proposal_included(self, mock_league_class):
        txn = {
            "id": "trade-1",
            "type": "TRADE_PROPOSAL",
            "status": "PENDING",
            "teamId": 1,
            "scoringPeriodId": 5,
            "comment": "Deal?",
            "expirationDate": 1773082242411,
            "teamActions": {"1": "ACCEPTED"},
            "items": [
                {"playerId": 100, "type": "TRADE", "fromTeamId": 1, "toTeamId": 2},
                {"playerId": 200, "type": "TRADE", "fromTeamId": 2, "toTeamId": 1},
            ],
        }
        league = _make_league_with_transactions([txn])
        mock_league_class.return_value = league

        from espn_fantasy_mcp.espn_client import ESPNClient

        client = ESPNClient(league_id="123456", espn_s2="s2", swid="{swid}")
        result = client.get_pending_transactions()

        assert len(result["pending_trades"]) == 1
        t = result["pending_trades"][0]
        assert t["transaction_id"] == "trade-1"
        assert t["type"] == "TRADE_PROPOSAL"
        assert t["status"] == "PENDING"
        assert t["is_pending_vote"] is False
        assert t["comment"] == "Deal?"
        assert len(t["items"]) == 2

    @patch("espn_fantasy_mcp.espn_client.League")
    def test_superseded_proposal_excluded(self, mock_league_class):
        """Original TRADE_PROPOSAL is skipped when a cancel/decline references it."""
        original = {
            "id": "trade-1",
            "type": "TRADE_PROPOSAL",
            "status": "PENDING",
            "teamId": 1,
            "scoringPeriodId": 5,
            "items": [{"playerId": 100, "type": "TRADE", "fromTeamId": 1, "toTeamId": 2}],
        }
        cancel = {
            "id": "cancel-1",
            "type": "TRADE_PROPOSAL",
            "status": "CANCELED",
            "teamId": 1,
            "scoringPeriodId": 5,
            "relatedTransactionId": "trade-1",
            "items": [{"playerId": 100, "type": "TRADE", "fromTeamId": 1, "toTeamId": 2}],
        }
        league = _make_league_with_transactions([original, cancel])
        mock_league_class.return_value = league

        from espn_fantasy_mcp.espn_client import ESPNClient

        client = ESPNClient(league_id="123456", espn_s2="s2", swid="{swid}")
        result = client.get_pending_transactions()

        # Only the cancellation appears, not the original
        assert len(result["pending_trades"]) == 1
        assert result["pending_trades"][0]["transaction_id"] == "cancel-1"
        assert result["pending_trades"][0]["status"] == "CANCELED"

    @patch("espn_fantasy_mcp.espn_client.League")
    def test_trade_accept_shown_with_items_from_original(self, mock_league_class):
        """TRADE_ACCEPT is included with items sourced from the original proposal."""
        original = {
            "id": "trade-1",
            "type": "TRADE_PROPOSAL",
            "status": "PENDING",
            "teamId": 1,
            "scoringPeriodId": 5,
            "items": [
                {"playerId": 100, "type": "TRADE", "fromTeamId": 1, "toTeamId": 2},
                {"playerId": 200, "type": "TRADE", "fromTeamId": 2, "toTeamId": 1},
            ],
        }
        accept = {
            "id": "accept-1",
            "type": "TRADE_ACCEPT",
            "status": "PENDING",
            "teamId": 2,
            "scoringPeriodId": 5,
            "relatedTransactionId": "trade-1",
            "items": [],  # TRADE_ACCEPT carries no items
        }
        league = _make_league_with_transactions([original, accept])
        mock_league_class.return_value = league

        from espn_fantasy_mcp.espn_client import ESPNClient

        client = ESPNClient(league_id="123456", espn_s2="s2", swid="{swid}")
        result = client.get_pending_transactions()

        # Original superseded; only TRADE_ACCEPT remains
        assert len(result["pending_trades"]) == 1
        t = result["pending_trades"][0]
        assert t["transaction_id"] == "accept-1"
        assert t["type"] == "TRADE_ACCEPT"
        assert t["is_pending_vote"] is True
        # Items must come from the original proposal
        assert len(t["items"]) == 2
        player_ids = {item["player_id"] for item in t["items"]}
        assert player_ids == {100, 200}
        # proposing_team_id should come from the original, not the accepting team
        assert t["proposing_team_id"] == 1

    @patch("espn_fantasy_mcp.espn_client.League")
    def test_trade_accept_missing_original_has_none_proposing_team(self, mock_league_class):
        """TRADE_ACCEPT with no matching original sets proposing_team_id to None."""
        accept = {
            "id": "accept-orphan",
            "type": "TRADE_ACCEPT",
            "status": "PENDING",
            "teamId": 2,
            "scoringPeriodId": 5,
            "relatedTransactionId": "nonexistent-id",
            "items": [],
        }
        league = _make_league_with_transactions([accept])
        mock_league_class.return_value = league

        from espn_fantasy_mcp.espn_client import ESPNClient

        client = ESPNClient(league_id="123456", espn_s2="s2", swid="{swid}")
        result = client.get_pending_transactions()

        assert len(result["pending_trades"]) == 1
        t = result["pending_trades"][0]
        assert t["proposing_team_id"] is None
        assert t["proposing_team_name"] is None
        assert t["items"] == []

    @patch("espn_fantasy_mcp.espn_client.League")
    def test_team_filter_excludes_unrelated_waivers(self, mock_league_class):
        """When team_id is given, waivers from other teams are excluded."""
        txn_mine = {
            "id": "waiver-1",
            "type": "WAIVER",
            "status": "PENDING",
            "teamId": 1,
            "bidAmount": 5,
            "scoringPeriodId": 5,
            "items": [{"type": "ADD", "playerId": 200}],
        }
        txn_other = {
            "id": "waiver-2",
            "type": "WAIVER",
            "status": "PENDING",
            "teamId": 2,
            "bidAmount": 0,
            "scoringPeriodId": 5,
            "items": [{"type": "ADD", "playerId": 100}],
        }
        league = _make_league_with_transactions([txn_mine, txn_other])
        mock_league_class.return_value = league

        from espn_fantasy_mcp.espn_client import ESPNClient

        client = ESPNClient(league_id="123456", espn_s2="s2", swid="{swid}")
        # team index 1 maps to team_id=1 (first team in list)
        result = client.get_pending_transactions(team_id=1)

        assert len(result["pending_waivers"]) == 1
        assert result["pending_waivers"][0]["transaction_id"] == "waiver-1"

    @patch("espn_fantasy_mcp.espn_client.League")
    def test_team_filter_includes_trades_where_team_is_involved(self, mock_league_class):
        """Team filter keeps trades where the team appears in any item's fromTeamId or toTeamId."""
        txn = {
            "id": "trade-1",
            "type": "TRADE_PROPOSAL",
            "status": "PENDING",
            "teamId": 1,
            "scoringPeriodId": 5,
            "items": [
                {"playerId": 100, "type": "TRADE", "fromTeamId": 1, "toTeamId": 2},
                {"playerId": 200, "type": "TRADE", "fromTeamId": 2, "toTeamId": 1},
            ],
        }
        league = _make_league_with_transactions([txn])
        mock_league_class.return_value = league

        from espn_fantasy_mcp.espn_client import ESPNClient

        client = ESPNClient(league_id="123456", espn_s2="s2", swid="{swid}")
        # Filter for team index 2 (team_id=2, the receiving team)
        result = client.get_pending_transactions(team_id=2)

        assert len(result["pending_trades"]) == 1

    @patch("espn_fantasy_mcp.espn_client.League")
    def test_team_filter_excludes_unrelated_trades(self, mock_league_class):
        """Team filter excludes trades where the filtered team is not a party."""
        txn = {
            "id": "trade-1",
            "type": "TRADE_PROPOSAL",
            "status": "PENDING",
            "teamId": 1,
            "scoringPeriodId": 5,
            "items": [
                {"playerId": 100, "type": "TRADE", "fromTeamId": 1, "toTeamId": 2},
            ],
        }
        league = _make_league_with_transactions([txn])
        # Add a third team that is not involved in the trade
        team_c = Mock()
        team_c.team_id = 3
        team_c.team_name = "Team C"
        league.teams.append(team_c)
        mock_league_class.return_value = league

        from espn_fantasy_mcp.espn_client import ESPNClient

        client = ESPNClient(league_id="123456", espn_s2="s2", swid="{swid}")
        # Filter for team index 3 (team_id=3, not involved)
        result = client.get_pending_transactions(team_id=3)

        assert len(result["pending_trades"]) == 0

    @patch("espn_fantasy_mcp.espn_client.League")
    def test_no_transactions_key_returns_empty(self, mock_league_class):
        """If ESPN API returns no 'transactions' key, returns empty lists."""
        league = Mock()
        league.currentMatchupPeriod = 5
        league.teams = []
        league.espn_request.league_get.return_value = {}
        mock_league_class.return_value = league

        from espn_fantasy_mcp.espn_client import ESPNClient

        client = ESPNClient(league_id="123456", espn_s2="s2", swid="{swid}")
        result = client.get_pending_transactions()

        assert result == {"pending_waivers": [], "pending_trades": []}


# ---------------------------------------------------------------------------
# get_pending_transactions – MCP tool handler
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGetPendingTransactionsTool:
    def test_tool_is_registered(self):
        names = [t.name for t in transaction_tools.get_tools()]
        assert "get_pending_transactions" in names

    def test_team_id_not_required(self):
        tool = next(
            t for t in transaction_tools.get_tools() if t.name == "get_pending_transactions"
        )
        assert tool.inputSchema.get("required", []) == []

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_returns_waiver_and_trade_counts(self, mock_client_class, mock_env_vars):
        client = Mock()
        client.get_pending_transactions.return_value = {
            "pending_waivers": [{"transaction_id": "w1", "status": "PENDING"}],
            "pending_trades": [{"transaction_id": "t1", "status": "PENDING"}],
        }
        client.get_team.return_value = Mock(team_name="My Team")
        mock_client_class.return_value = client

        result = await transaction_tools.handle_get_pending_transactions(
            {
                "league_id": "123456",
                "team_id": 1,
            }
        )

        response = json.loads(result)
        assert response["success"] is True
        assert response["pending_waiver_count"] == 1
        assert response["pending_trade_count"] == 1

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_passes_team_id_to_client(self, mock_client_class, mock_env_vars):
        client = Mock()
        client.get_pending_transactions.return_value = {
            "pending_waivers": [],
            "pending_trades": [],
        }
        client.get_team.return_value = Mock(team_name="My Team")
        mock_client_class.return_value = client

        await transaction_tools.handle_get_pending_transactions(
            {
                "league_id": "123456",
                "team_id": 3,
            }
        )

        client.get_pending_transactions.assert_called_once_with(team_id=3)

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_no_team_id_passes_none(self, mock_client_class, mock_env_vars):
        client = Mock()
        client.get_pending_transactions.return_value = {
            "pending_waivers": [],
            "pending_trades": [],
        }
        mock_client_class.return_value = client

        await transaction_tools.handle_get_pending_transactions({"league_id": "123456"})

        client.get_pending_transactions.assert_called_once_with(team_id=None)

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.transaction_tools.ESPNClient")
    async def test_error_returns_failure_response(self, mock_client_class, mock_env_vars):
        client = Mock()
        client.get_pending_transactions.side_effect = RuntimeError("ESPN unavailable")
        mock_client_class.return_value = client

        result = await transaction_tools.handle_get_pending_transactions(
            {
                "league_id": "123456",
            }
        )

        response = json.loads(result)
        assert response["success"] is False
        assert response["error"] == "RuntimeError"
