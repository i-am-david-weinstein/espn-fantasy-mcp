"""Tests for player tools."""
import pytest
import json
from unittest.mock import patch, Mock
from espn_fantasy_mcp.tools import player_tools
from espn_fantasy_mcp.models import Player, RosterStatus


@pytest.mark.unit
class TestPlayerTools:
    """Tests for player tool functions."""

    def test_get_tools(self):
        """Test that get_tools returns correct tool definitions."""
        tools = player_tools.get_tools()

        assert len(tools) == 2
        assert tools[0].name == "get_free_agents"
        assert tools[1].name == "get_player_info"

    @pytest.mark.asyncio
    async def test_handle_tool_unknown(self):
        """Test handle_tool with unknown tool name."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await player_tools.handle_tool("unknown_tool", {})

    @pytest.mark.asyncio
    @patch('espn_fantasy_mcp.tools.player_tools.ESPNClient')
    async def test_handle_get_free_agents_success(self, mock_client_class, mock_env_vars):
        """Test handle_get_free_agents with successful response."""
        # Mock the client and its methods
        mock_client = Mock()
        mock_player = Player(
            player_id=12345,
            name="Free Agent Player",
            team="NYY",
            position="SS",
            roster_status=RosterStatus.FREE_AGENT
        )
        mock_client.get_free_agents.return_value = [mock_player]
        mock_client_class.return_value = mock_client

        result = await player_tools.handle_get_free_agents({
            "league_id": "123456",
            "season_year": 2024,
            "size": 50
        })

        response = json.loads(result)
        assert response["success"] is True
        assert len(response["data"]) == 1
        assert response["data"][0]["name"] == "Free Agent Player"

    @pytest.mark.asyncio
    @patch('espn_fantasy_mcp.tools.player_tools.ESPNClient')
    async def test_handle_get_free_agents_with_position(self, mock_client_class, mock_env_vars):
        """Test handle_get_free_agents with position filter."""
        mock_client = Mock()
        mock_client.get_free_agents.return_value = []
        mock_client_class.return_value = mock_client

        result = await player_tools.handle_get_free_agents({
            "league_id": "123456",
            "position": "OF",
            "size": 20
        })

        mock_client.get_free_agents.assert_called_once_with(size=20, position="OF")
        response = json.loads(result)
        assert response["success"] is True

    @pytest.mark.asyncio
    async def test_handle_get_free_agents_missing_league_id(self, monkeypatch):
        """Test handle_get_free_agents without league_id."""
        monkeypatch.delenv("ESPN_LEAGUE_ID", raising=False)

        # Need to reload the config module to pick up the change
        import importlib
        import espn_fantasy_mcp.config
        importlib.reload(espn_fantasy_mcp.config)

        with pytest.raises(ValueError, match="league_id is required"):
            await player_tools.handle_get_free_agents({})

    @pytest.mark.asyncio
    @patch('espn_fantasy_mcp.tools.player_tools.ESPNClient')
    async def test_handle_get_free_agents_error(self, mock_client_class, mock_env_vars):
        """Test handle_get_free_agents with error."""
        # Mock the client instance and make the method raise an exception
        mock_client = Mock()
        mock_client.get_free_agents.side_effect = ConnectionError("API connection failed")
        mock_client_class.return_value = mock_client

        result = await player_tools.handle_get_free_agents({
            "league_id": "123456"
        })

        response = json.loads(result)
        assert response["success"] is False
        assert response["error"] == "ConnectionError"
        assert "API connection failed" in response["message"]

    @pytest.mark.asyncio
    @patch('espn_fantasy_mcp.tools.player_tools.ESPNClient')
    async def test_handle_get_player_info_success(self, mock_client_class, mock_env_vars):
        """Test handle_get_player_info with successful response."""
        mock_client = Mock()
        mock_player = Player(
            player_id=30836,
            name="Aaron Judge",
            team="NYY",
            position="OF",
            roster_status=RosterStatus.ROSTERED,
            fantasy_team_id=0,
            fantasy_team_name="Test Team"
        )
        mock_client.get_player_by_name.return_value = (mock_player, [])
        mock_client_class.return_value = mock_client

        result = await player_tools.handle_get_player_info({
            "player_name": "Aaron Judge",
            "league_id": "123456"
        })

        response = json.loads(result)
        assert response["success"] is True
        assert response["data"]["name"] == "Aaron Judge"
        assert response["data"]["player_id"] == 30836

    @pytest.mark.asyncio
    @patch('espn_fantasy_mcp.tools.player_tools.ESPNClient')
    async def test_handle_get_player_info_not_found_with_suggestions(
        self, mock_client_class, mock_env_vars
    ):
        """Test handle_get_player_info when player not found but suggestions available."""
        mock_client = Mock()
        mock_client.get_player_by_name.return_value = (None, ["Aaron Judge", "Aaron Nola"])
        mock_client_class.return_value = mock_client

        result = await player_tools.handle_get_player_info({
            "player_name": "Arron Judge",
            "league_id": "123456"
        })

        response = json.loads(result)
        assert response["success"] is False
        assert response["error"] == "PlayerNotFound"
        assert "not found" in response["message"]
        assert len(response["suggestions"]) == 2

    @pytest.mark.asyncio
    async def test_handle_get_player_info_missing_player_name(self):
        """Test handle_get_player_info without player_name."""
        with pytest.raises(ValueError, match="player_name is required"):
            await player_tools.handle_get_player_info({
                "league_id": "123456"
            })

    @pytest.mark.asyncio
    async def test_handle_get_player_info_missing_league_id(self, monkeypatch):
        """Test handle_get_player_info without league_id."""
        monkeypatch.delenv("ESPN_LEAGUE_ID", raising=False)

        # Need to reload the config module to pick up the change
        import importlib
        import espn_fantasy_mcp.config
        importlib.reload(espn_fantasy_mcp.config)

        with pytest.raises(ValueError, match="league_id is required"):
            await player_tools.handle_get_player_info({
                "player_name": "Aaron Judge"
            })

    @pytest.mark.asyncio
    @patch('espn_fantasy_mcp.tools.player_tools.ESPNClient')
    async def test_handle_get_player_info_error(self, mock_client_class, mock_env_vars):
        """Test handle_get_player_info with error."""
        # Mock the client instance and make the method raise an exception
        mock_client = Mock()
        mock_client.get_player_by_name.side_effect = ValueError("Invalid league ID")
        mock_client_class.return_value = mock_client

        result = await player_tools.handle_get_player_info({
            "player_name": "Aaron Judge",
            "league_id": "invalid"
        })

        response = json.loads(result)
        assert response["success"] is False
        assert response["error"] == "ValueError"
        assert "Invalid league ID" in response["message"]
