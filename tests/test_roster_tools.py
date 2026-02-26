"""Tests for roster tools."""
import pytest
import json
from unittest.mock import patch, Mock
from espn_fantasy_mcp.tools import roster_tools


# Stable slot ID -> name mapping used across roster tool tests
MOCK_POSITION_MAP = {0: "C", 2: "1B", 16: "BE", 17: "IL"}


@pytest.mark.unit
class TestRosterToolsGetTools:
    """Tests for get_tools function."""

    def test_get_tools_returns_one_tool(self):
        """Test that get_tools returns exactly one tool."""
        tools = roster_tools.get_tools()
        assert len(tools) == 1

    def test_get_tools_modify_lineup_name(self):
        """Test that the returned tool is named modify_lineup."""
        tools = roster_tools.get_tools()
        assert tools[0].name == "modify_lineup"

    def test_get_tools_schema_required_fields(self):
        """Test that modify_lineup schema has required fields."""
        tools = roster_tools.get_tools()
        schema = tools[0].inputSchema
        assert "team_id" in schema["required"]
        assert "moves" in schema["required"]

    def test_get_tools_schema_moves_is_array(self):
        """Test that modify_lineup schema defines moves as an array."""
        tools = roster_tools.get_tools()
        assert tools[0].inputSchema["properties"]["moves"]["type"] == "array"

    def test_get_tools_schema_confirm_defaults_to_false(self):
        """Test that modify_lineup schema includes confirm field defaulting to False."""
        tools = roster_tools.get_tools()
        assert tools[0].inputSchema["properties"]["confirm"]["default"] is False


@pytest.mark.unit
class TestRosterToolsHandleTool:
    """Tests for handle_tool dispatch function."""

    @pytest.mark.asyncio
    async def test_handle_tool_unknown_raises(self):
        """Test handle_tool with unknown tool name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await roster_tools.handle_tool("unknown_tool", {})

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.roster_tools.ESPNClient")
    @patch("espn_fantasy_mcp.tools.roster_tools.POSITION_MAP", MOCK_POSITION_MAP)
    async def test_handle_tool_dispatches_modify_lineup(
        self, mock_client_class, mock_espn_client, mock_player, mock_env_vars
    ):
        """Test that handle_tool routes modify_lineup to the correct handler."""
        mock_espn_client.get_roster.return_value = [mock_player(player_id=111, lineup_slot="BE")]
        mock_client_class.return_value = mock_espn_client

        result = await roster_tools.handle_tool("modify_lineup", {
            "league_id": "123456",
            "team_id": 0,
            "moves": [{"player_id": 111, "from_slot": 16, "to_slot": 0}],
        })

        response = json.loads(result)
        assert response["success"] is True
        assert response["preview"] is True


@pytest.mark.unit
class TestHandleModifyLineupValidation:
    """Tests for input validation in handle_modify_lineup."""

    @pytest.mark.asyncio
    async def test_missing_league_id_raises(self, monkeypatch):
        """Test that missing league_id raises ValueError."""
        monkeypatch.delenv("ESPN_LEAGUE_ID", raising=False)

        import importlib
        import espn_fantasy_mcp.config
        importlib.reload(espn_fantasy_mcp.config)

        with pytest.raises(ValueError, match="league_id is required"):
            await roster_tools.handle_modify_lineup({
                "team_id": 0,
                "moves": [{"player_id": 1, "from_slot": 16, "to_slot": 0}],
            })

    @pytest.mark.asyncio
    async def test_missing_team_id_raises(self, mock_env_vars):
        """Test that missing team_id raises ValueError."""
        with pytest.raises(ValueError, match="team_id is required"):
            await roster_tools.handle_modify_lineup({
                "league_id": "123456",
                "moves": [{"player_id": 1, "from_slot": 16, "to_slot": 0}],
            })

    @pytest.mark.asyncio
    async def test_missing_moves_raises(self, mock_env_vars):
        """Test that missing moves raises ValueError."""
        with pytest.raises(ValueError, match="moves array is required"):
            await roster_tools.handle_modify_lineup({
                "league_id": "123456",
                "team_id": 0,
            })

    @pytest.mark.asyncio
    async def test_empty_moves_raises(self, mock_env_vars):
        """Test that empty moves list raises ValueError."""
        with pytest.raises(ValueError, match="moves array is required"):
            await roster_tools.handle_modify_lineup({
                "league_id": "123456",
                "team_id": 0,
                "moves": [],
            })


@pytest.mark.unit
class TestHandleModifyLineupPreview:
    """Tests for preview mode (confirm=False) in handle_modify_lineup."""

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.roster_tools.ESPNClient")
    @patch("espn_fantasy_mcp.tools.roster_tools.POSITION_MAP", MOCK_POSITION_MAP)
    async def test_preview_success(
        self, mock_client_class, mock_espn_client, mock_player, mock_env_vars
    ):
        """Test preview mode returns success with preview flag."""
        mock_espn_client.get_roster.return_value = [mock_player(player_id=111, lineup_slot="BE")]
        mock_client_class.return_value = mock_espn_client

        result = await roster_tools.handle_modify_lineup({
            "league_id": "123456",
            "team_id": 0,
            "moves": [{"player_id": 111, "from_slot": 16, "to_slot": 0}],
            "confirm": False,
        })

        response = json.loads(result)
        assert response["success"] is True
        assert response["preview"] is True

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.roster_tools.ESPNClient")
    @patch("espn_fantasy_mcp.tools.roster_tools.POSITION_MAP", MOCK_POSITION_MAP)
    async def test_preview_does_not_execute(
        self, mock_client_class, mock_espn_client, mock_player, mock_env_vars
    ):
        """Test that preview mode does not call client.modify_lineup."""
        mock_espn_client.get_roster.return_value = [mock_player(player_id=111, lineup_slot="BE")]
        mock_client_class.return_value = mock_espn_client

        await roster_tools.handle_modify_lineup({
            "league_id": "123456",
            "team_id": 0,
            "moves": [{"player_id": 111, "from_slot": 16, "to_slot": 0}],
        })

        mock_espn_client.modify_lineup.assert_not_called()

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.roster_tools.ESPNClient")
    @patch("espn_fantasy_mcp.tools.roster_tools.POSITION_MAP", MOCK_POSITION_MAP)
    async def test_preview_includes_move_details(
        self, mock_client_class, mock_espn_client, mock_player, mock_env_vars
    ):
        """Test preview response includes correct move details."""
        mock_espn_client.get_roster.return_value = [
            mock_player(player_id=111, name="Aaron Judge", lineup_slot="BE", position="OF")
        ]
        mock_client_class.return_value = mock_espn_client

        result = await roster_tools.handle_modify_lineup({
            "league_id": "123456",
            "team_id": 0,
            "moves": [{"player_id": 111, "from_slot": 16, "to_slot": 0}],
        })

        response = json.loads(result)
        assert len(response["moves"]) == 1
        move = response["moves"][0]
        assert move["player_id"] == 111
        assert move["player_name"] == "Aaron Judge"
        assert move["from_slot"] == 16
        assert move["from_slot_name"] == "BE"
        assert move["to_slot"] == 0
        assert move["to_slot_name"] == "C"
        assert move["position"] == "OF"

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.roster_tools.ESPNClient")
    @patch("espn_fantasy_mcp.tools.roster_tools.POSITION_MAP", MOCK_POSITION_MAP)
    async def test_preview_includes_team_info(
        self, mock_client_class, mock_espn_client, mock_player, mock_env_vars
    ):
        """Test preview response includes team name and id."""
        mock_espn_client.get_roster.return_value = [mock_player(player_id=111, lineup_slot="BE")]
        mock_espn_client.get_team.return_value = Mock(team_name="Best Team")
        mock_client_class.return_value = mock_espn_client

        result = await roster_tools.handle_modify_lineup({
            "league_id": "123456",
            "team_id": 2,
            "moves": [{"player_id": 111, "from_slot": 16, "to_slot": 0}],
        })

        response = json.loads(result)
        assert response["team_name"] == "Best Team"
        assert response["team_id"] == 2

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.roster_tools.ESPNClient")
    @patch("espn_fantasy_mcp.tools.roster_tools.POSITION_MAP", MOCK_POSITION_MAP)
    async def test_preview_uses_provided_scoring_period(
        self, mock_client_class, mock_espn_client, mock_player, mock_env_vars
    ):
        """Test preview uses provided scoring_period_id over currentMatchupPeriod."""
        mock_espn_client.get_roster.return_value = [mock_player(player_id=111, lineup_slot="BE")]
        mock_client_class.return_value = mock_espn_client

        result = await roster_tools.handle_modify_lineup({
            "league_id": "123456",
            "team_id": 0,
            "moves": [{"player_id": 111, "from_slot": 16, "to_slot": 0}],
            "scoring_period_id": 10,
        })

        response = json.loads(result)
        assert response["scoring_period_id"] == 10

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.roster_tools.ESPNClient")
    @patch("espn_fantasy_mcp.tools.roster_tools.POSITION_MAP", MOCK_POSITION_MAP)
    async def test_preview_falls_back_to_current_matchup_period(
        self, mock_client_class, mock_espn_client, mock_player, mock_env_vars
    ):
        """Test preview uses currentMatchupPeriod when scoring_period_id not provided."""
        mock_espn_client.get_roster.return_value = [mock_player(player_id=111, lineup_slot="BE")]
        mock_espn_client.league.currentMatchupPeriod = 7
        mock_client_class.return_value = mock_espn_client

        result = await roster_tools.handle_modify_lineup({
            "league_id": "123456",
            "team_id": 0,
            "moves": [{"player_id": 111, "from_slot": 16, "to_slot": 0}],
        })

        response = json.loads(result)
        assert response["scoring_period_id"] == 7

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.roster_tools.ESPNClient")
    @patch("espn_fantasy_mcp.tools.roster_tools.POSITION_MAP", MOCK_POSITION_MAP)
    async def test_preview_includes_confirm_instructions(
        self, mock_client_class, mock_espn_client, mock_player, mock_env_vars
    ):
        """Test preview response includes instructions to set confirm=true."""
        mock_espn_client.get_roster.return_value = [mock_player(player_id=111, lineup_slot="BE")]
        mock_client_class.return_value = mock_espn_client

        result = await roster_tools.handle_modify_lineup({
            "league_id": "123456",
            "team_id": 0,
            "moves": [{"player_id": 111, "from_slot": 16, "to_slot": 0}],
        })

        response = json.loads(result)
        assert "confirm=true" in response["instructions"]

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.roster_tools.ESPNClient")
    @patch("espn_fantasy_mcp.tools.roster_tools.POSITION_MAP", MOCK_POSITION_MAP)
    async def test_preview_multiple_moves(
        self, mock_client_class, mock_espn_client, mock_player, mock_env_vars
    ):
        """Test preview with multiple moves returns all move details."""
        mock_espn_client.get_roster.return_value = [
            mock_player(player_id=111, name="Player One", lineup_slot="BE", position="OF"),
            mock_player(player_id=222, name="Player Two", lineup_slot="C", position="C"),
        ]
        mock_client_class.return_value = mock_espn_client

        result = await roster_tools.handle_modify_lineup({
            "league_id": "123456",
            "team_id": 0,
            "moves": [
                {"player_id": 111, "from_slot": 16, "to_slot": 0},
                {"player_id": 222, "from_slot": 0, "to_slot": 16},
            ],
        })

        response = json.loads(result)
        assert response["success"] is True
        assert len(response["moves"]) == 2


@pytest.mark.unit
class TestHandleModifyLineupMoveValidationErrors:
    """Tests for per-move validation errors in handle_modify_lineup."""

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.roster_tools.ESPNClient")
    @patch("espn_fantasy_mcp.tools.roster_tools.POSITION_MAP", MOCK_POSITION_MAP)
    async def test_player_not_on_roster(
        self, mock_client_class, mock_espn_client, mock_player, mock_env_vars
    ):
        """Test that a move for a player not on the roster returns a validation error."""
        mock_espn_client.get_roster.return_value = [mock_player(player_id=111, lineup_slot="BE")]
        mock_client_class.return_value = mock_espn_client

        result = await roster_tools.handle_modify_lineup({
            "league_id": "123456",
            "team_id": 0,
            "moves": [{"player_id": 999, "from_slot": 16, "to_slot": 0}],
        })

        response = json.loads(result)
        assert response["success"] is False
        assert response["error"] == "ValidationError"
        assert len(response["validation_errors"]) == 1
        assert "999" in response["validation_errors"][0]

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.roster_tools.ESPNClient")
    @patch("espn_fantasy_mcp.tools.roster_tools.POSITION_MAP", MOCK_POSITION_MAP)
    async def test_wrong_from_slot(
        self, mock_client_class, mock_espn_client, mock_player, mock_env_vars
    ):
        """Test that a from_slot not matching the player's current slot returns a validation error."""
        # Player is in "C" (slot 0), but move says from_slot=16 (BE)
        mock_espn_client.get_roster.return_value = [
            mock_player(player_id=111, name="Test Player", lineup_slot="C")
        ]
        mock_client_class.return_value = mock_espn_client

        result = await roster_tools.handle_modify_lineup({
            "league_id": "123456",
            "team_id": 0,
            "moves": [{"player_id": 111, "from_slot": 16, "to_slot": 0}],
        })

        response = json.loads(result)
        assert response["success"] is False
        assert response["error"] == "ValidationError"
        assert "Test Player" in response["validation_errors"][0]

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.roster_tools.ESPNClient")
    @patch("espn_fantasy_mcp.tools.roster_tools.POSITION_MAP", MOCK_POSITION_MAP)
    async def test_multiple_validation_errors_all_reported(
        self, mock_client_class, mock_espn_client, mock_player, mock_env_vars
    ):
        """Test that all invalid moves produce validation errors, not just the first."""
        mock_espn_client.get_roster.return_value = [
            mock_player(player_id=111, name="Player One", lineup_slot="C")
        ]
        mock_client_class.return_value = mock_espn_client

        result = await roster_tools.handle_modify_lineup({
            "league_id": "123456",
            "team_id": 0,
            "moves": [
                {"player_id": 999, "from_slot": 16, "to_slot": 0},   # not on roster
                {"player_id": 111, "from_slot": 16, "to_slot": 0},   # wrong from_slot
            ],
        })

        response = json.loads(result)
        assert response["success"] is False
        assert len(response["validation_errors"]) == 2

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.roster_tools.ESPNClient")
    @patch("espn_fantasy_mcp.tools.roster_tools.POSITION_MAP", MOCK_POSITION_MAP)
    async def test_validation_error_blocks_execution(
        self, mock_client_class, mock_espn_client, mock_env_vars
    ):
        """Test that validation errors prevent execution even when confirm=True."""
        mock_espn_client.get_roster.return_value = []
        mock_client_class.return_value = mock_espn_client

        result = await roster_tools.handle_modify_lineup({
            "league_id": "123456",
            "team_id": 0,
            "moves": [{"player_id": 999, "from_slot": 16, "to_slot": 0}],
            "confirm": True,
        })

        response = json.loads(result)
        assert response["success"] is False
        mock_espn_client.modify_lineup.assert_not_called()


@pytest.mark.unit
class TestHandleModifyLineupExecute:
    """Tests for execute mode (confirm=True) in handle_modify_lineup."""

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.roster_tools.ESPNClient")
    @patch("espn_fantasy_mcp.tools.roster_tools.POSITION_MAP", MOCK_POSITION_MAP)
    async def test_execute_success(
        self, mock_client_class, mock_espn_client, mock_player, mock_env_vars
    ):
        """Test that confirm=True executes lineup change and returns result."""
        mock_espn_client.get_roster.return_value = [mock_player(player_id=111, lineup_slot="BE")]
        mock_client_class.return_value = mock_espn_client

        result = await roster_tools.handle_modify_lineup({
            "league_id": "123456",
            "team_id": 0,
            "moves": [{"player_id": 111, "from_slot": 16, "to_slot": 0}],
            "confirm": True,
        })

        response = json.loads(result)
        assert response["success"] is True
        assert response["executed"] is True
        assert response["transaction_id"] == "txn-abc123"
        assert response["status"] == "EXECUTED"

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.roster_tools.ESPNClient")
    @patch("espn_fantasy_mcp.tools.roster_tools.POSITION_MAP", MOCK_POSITION_MAP)
    async def test_execute_calls_modify_lineup_with_correct_args(
        self, mock_client_class, mock_espn_client, mock_player, mock_env_vars
    ):
        """Test that execute passes the right arguments to client.modify_lineup."""
        mock_espn_client.get_roster.return_value = [mock_player(player_id=111, lineup_slot="BE")]
        mock_client_class.return_value = mock_espn_client

        moves = [{"player_id": 111, "from_slot": 16, "to_slot": 0}]
        await roster_tools.handle_modify_lineup({
            "league_id": "123456",
            "team_id": 3,
            "moves": moves,
            "scoring_period_id": 4,
            "confirm": True,
        })

        mock_espn_client.modify_lineup.assert_called_once_with(
            team_id=3,
            moves=moves,
            scoring_period_id=4,
        )

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.roster_tools.ESPNClient")
    @patch("espn_fantasy_mcp.tools.roster_tools.POSITION_MAP", MOCK_POSITION_MAP)
    async def test_execute_passes_none_scoring_period_when_not_provided(
        self, mock_client_class, mock_espn_client, mock_player, mock_env_vars
    ):
        """Test that omitting scoring_period_id passes None so the client uses its default."""
        mock_espn_client.get_roster.return_value = [mock_player(player_id=111, lineup_slot="BE")]
        mock_client_class.return_value = mock_espn_client

        await roster_tools.handle_modify_lineup({
            "league_id": "123456",
            "team_id": 0,
            "moves": [{"player_id": 111, "from_slot": 16, "to_slot": 0}],
            "confirm": True,
        })

        mock_espn_client.modify_lineup.assert_called_once_with(
            team_id=0,
            moves=[{"player_id": 111, "from_slot": 16, "to_slot": 0}],
            scoring_period_id=None,
        )

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.roster_tools.ESPNClient")
    @patch("espn_fantasy_mcp.tools.roster_tools.POSITION_MAP", MOCK_POSITION_MAP)
    async def test_execute_includes_move_details_and_raw_response(
        self, mock_client_class, mock_espn_client, mock_player, mock_env_vars
    ):
        """Test execute response includes move details and raw ESPN API response."""
        raw_api_response = {"id": "txn-xyz", "status": "EXECUTED", "scoringPeriodId": 2, "extra": "data"}
        mock_espn_client.get_roster.return_value = [
            mock_player(player_id=111, name="Aaron Judge", lineup_slot="BE", position="OF")
        ]
        mock_espn_client.modify_lineup.return_value = raw_api_response
        mock_client_class.return_value = mock_espn_client

        result = await roster_tools.handle_modify_lineup({
            "league_id": "123456",
            "team_id": 0,
            "moves": [{"player_id": 111, "from_slot": 16, "to_slot": 0}],
            "confirm": True,
        })

        response = json.loads(result)
        assert response["moves"][0]["player_name"] == "Aaron Judge"
        assert response["raw_response"] == raw_api_response
        assert response["scoring_period_id"] == 2


@pytest.mark.unit
class TestHandleModifyLineupErrorHandling:
    """Tests for exception handling in handle_modify_lineup."""

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.roster_tools.ESPNClient")
    async def test_connection_error(self, mock_client_class, mock_espn_client, mock_env_vars):
        """Test that ConnectionError from client returns a failure response."""
        mock_espn_client.get_roster.side_effect = ConnectionError("API unavailable")
        mock_client_class.return_value = mock_espn_client

        result = await roster_tools.handle_modify_lineup({
            "league_id": "123456",
            "team_id": 0,
            "moves": [{"player_id": 111, "from_slot": 16, "to_slot": 0}],
        })

        response = json.loads(result)
        assert response["success"] is False
        assert response["error"] == "ConnectionError"
        assert "API unavailable" in response["message"]

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.roster_tools.ESPNClient")
    async def test_index_error_invalid_team_id(self, mock_client_class, mock_espn_client, mock_env_vars):
        """Test that IndexError (e.g. invalid team_id) returns a failure response."""
        mock_espn_client.get_roster.side_effect = IndexError("list index out of range")
        mock_client_class.return_value = mock_espn_client

        result = await roster_tools.handle_modify_lineup({
            "league_id": "123456",
            "team_id": 99,
            "moves": [{"player_id": 111, "from_slot": 16, "to_slot": 0}],
        })

        response = json.loads(result)
        assert response["success"] is False
        assert response["error"] == "IndexError"

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.roster_tools.ESPNClient")
    async def test_attribute_error(self, mock_client_class, mock_espn_client, mock_env_vars):
        """Test that AttributeError returns a failure response."""
        mock_espn_client.get_roster.side_effect = AttributeError("object has no attribute")
        mock_client_class.return_value = mock_espn_client

        result = await roster_tools.handle_modify_lineup({
            "league_id": "123456",
            "team_id": 0,
            "moves": [{"player_id": 111, "from_slot": 16, "to_slot": 0}],
        })

        response = json.loads(result)
        assert response["success"] is False
        assert response["error"] == "AttributeError"

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.roster_tools.ESPNClient")
    async def test_generic_exception_prefixes_message(self, mock_client_class, mock_espn_client, mock_env_vars):
        """Test that unexpected exceptions return failure with 'Failed to modify lineup' prefix."""
        mock_espn_client.get_roster.side_effect = RuntimeError("unexpected error")
        mock_client_class.return_value = mock_espn_client

        result = await roster_tools.handle_modify_lineup({
            "league_id": "123456",
            "team_id": 0,
            "moves": [{"player_id": 111, "from_slot": 16, "to_slot": 0}],
        })

        response = json.loads(result)
        assert response["success"] is False
        assert response["error"] == "RuntimeError"
        assert "Failed to modify lineup" in response["message"]
        assert "unexpected error" in response["message"]

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.roster_tools.ESPNClient")
    @patch("espn_fantasy_mcp.tools.roster_tools.POSITION_MAP", MOCK_POSITION_MAP)
    async def test_api_error_during_execution(
        self, mock_client_class, mock_espn_client, mock_player, mock_env_vars
    ):
        """Test that ESPN API error during execution (confirm=True) returns failure response."""
        mock_espn_client.get_roster.return_value = [mock_player(player_id=111, lineup_slot="BE")]
        mock_espn_client.modify_lineup.side_effect = ConnectionError("ESPN API rejected request")
        mock_client_class.return_value = mock_espn_client

        result = await roster_tools.handle_modify_lineup({
            "league_id": "123456",
            "team_id": 0,
            "moves": [{"player_id": 111, "from_slot": 16, "to_slot": 0}],
            "confirm": True,
        })

        response = json.loads(result)
        assert response["success"] is False
        assert response["error"] == "ConnectionError"


@pytest.mark.unit
class TestHandleModifyLineupDefaults:
    """Tests for config-driven defaults in handle_modify_lineup."""

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.roster_tools.ESPNClient")
    @patch("espn_fantasy_mcp.tools.roster_tools.POSITION_MAP", MOCK_POSITION_MAP)
    async def test_uses_default_league_id_from_config(
        self, mock_client_class, mock_player, mock_espn_client, monkeypatch
    ):
        """Test that league_id defaults to the configured value when not provided."""
        import espn_fantasy_mcp.tools.roster_tools as rt
        monkeypatch.setattr(rt.Config, "ESPN_LEAGUE_ID", "123456")

        mock_espn_client.get_roster.return_value = [mock_player(player_id=111, lineup_slot="BE")]
        mock_client_class.return_value = mock_espn_client

        result = await roster_tools.handle_modify_lineup({
            "team_id": 0,
            "moves": [{"player_id": 111, "from_slot": 16, "to_slot": 0}],
        })

        response = json.loads(result)
        assert response["success"] is True
        assert mock_client_class.call_args.kwargs["league_id"] == "123456"

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.roster_tools.ESPNClient")
    @patch("espn_fantasy_mcp.tools.roster_tools.POSITION_MAP", MOCK_POSITION_MAP)
    async def test_uses_default_season_year_from_config(
        self, mock_client_class, mock_espn_client, mock_player, mock_env_vars
    ):
        """Test that season_year defaults to the configured value when not provided."""
        mock_espn_client.get_roster.return_value = [mock_player(player_id=111, lineup_slot="BE")]
        mock_client_class.return_value = mock_espn_client

        await roster_tools.handle_modify_lineup({
            "league_id": "123456",
            "team_id": 0,
            "moves": [{"player_id": 111, "from_slot": 16, "to_slot": 0}],
        })

        assert mock_client_class.call_args.kwargs["season_year"] == 2024

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.roster_tools.ESPNClient")
    @patch("espn_fantasy_mcp.tools.roster_tools.POSITION_MAP", MOCK_POSITION_MAP)
    async def test_omitting_confirm_defaults_to_preview(
        self, mock_client_class, mock_espn_client, mock_player, mock_env_vars
    ):
        """Test that omitting confirm defaults to preview mode (no execution)."""
        mock_espn_client.get_roster.return_value = [mock_player(player_id=111, lineup_slot="BE")]
        mock_client_class.return_value = mock_espn_client

        result = await roster_tools.handle_modify_lineup({
            "league_id": "123456",
            "team_id": 0,
            "moves": [{"player_id": 111, "from_slot": 16, "to_slot": 0}],
        })

        response = json.loads(result)
        assert response.get("preview") is True
        mock_espn_client.modify_lineup.assert_not_called()

    @pytest.mark.asyncio
    @patch("espn_fantasy_mcp.tools.roster_tools.POSITION_MAP", MOCK_POSITION_MAP)
    @patch("espn_fantasy_mcp.tools.roster_tools.ESPNClient")
    async def test_unknown_slot_id_falls_back_to_string(
        self, mock_client_class, mock_espn_client, mock_player, mock_env_vars
    ):
        """Test that slot IDs absent from POSITION_MAP fall back to their string representation."""
        # slot 999 is not in MOCK_POSITION_MAP, so from_slot_name should be "999"
        mock_espn_client.get_roster.return_value = [
            mock_player(player_id=111, lineup_slot="999")
        ]
        mock_client_class.return_value = mock_espn_client

        result = await roster_tools.handle_modify_lineup({
            "league_id": "123456",
            "team_id": 0,
            "moves": [{"player_id": 111, "from_slot": 999, "to_slot": 0}],
        })

        response = json.loads(result)
        assert response["success"] is True
        assert response["moves"][0]["from_slot_name"] == "999"
