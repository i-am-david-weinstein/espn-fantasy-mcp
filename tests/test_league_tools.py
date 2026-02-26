"""Tests for league tools."""
import pytest
import json
from unittest.mock import patch, Mock
from espn_fantasy_mcp.tools import league_tools
from espn_fantasy_mcp.models import LeagueSettings, Team


@pytest.mark.unit
class TestLeagueTools:
    """Tests for league tool functions."""

    def test_get_tools(self):
        """Test that get_tools returns correct tool definitions."""
        tools = league_tools.get_tools()

        assert len(tools) == 2
        assert tools[0].name == "get_league_settings"
        assert tools[1].name == "get_standings"

    @pytest.mark.asyncio
    async def test_handle_tool_unknown(self):
        """Test handle_tool with unknown tool name."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await league_tools.handle_tool("unknown_tool", {})

    @pytest.mark.asyncio
    @patch('espn_fantasy_mcp.tools.league_tools.ESPNClient')
    async def test_handle_get_league_settings_success(
        self, mock_client_class, mock_env_vars, sample_league_settings
    ):
        """Test handle_get_league_settings with successful response."""
        mock_client = Mock()
        mock_settings = LeagueSettings(**sample_league_settings)
        mock_client.get_league_settings.return_value = mock_settings
        mock_client_class.return_value = mock_client

        result = await league_tools.handle_get_league_settings({
            "league_id": "123456",
            "season_year": 2024
        })

        response = json.loads(result)
        assert response["success"] is True
        assert response["data"]["name"] == "Test Fantasy League"
        assert response["data"]["team_count"] == 12

    @pytest.mark.asyncio
    async def test_handle_get_league_settings_missing_league_id(self, monkeypatch):
        """Test handle_get_league_settings without league_id."""
        monkeypatch.delenv("ESPN_LEAGUE_ID", raising=False)

        import importlib
        import espn_fantasy_mcp.config
        importlib.reload(espn_fantasy_mcp.config)

        with pytest.raises(ValueError, match="league_id is required"):
            await league_tools.handle_get_league_settings({})

    @pytest.mark.asyncio
    @patch('espn_fantasy_mcp.tools.league_tools.Config')
    @patch('espn_fantasy_mcp.tools.league_tools.ESPNClient')
    async def test_handle_get_league_settings_uses_defaults(
        self, mock_client_class, mock_config, sample_league_settings
    ):
        """Test handle_get_league_settings uses default values from config."""
        # Mock Config methods
        mock_config.get_default_league_id.return_value = "123456"
        mock_config.get_default_season_year.return_value = 2024
        mock_config.ESPN_S2 = "test_s2"
        mock_config.ESPN_SWID = "{TEST-SWID}"

        mock_client = Mock()
        mock_settings = LeagueSettings(**sample_league_settings)
        mock_client.get_league_settings.return_value = mock_settings
        mock_client_class.return_value = mock_client

        # Call without explicit league_id or season_year
        result = await league_tools.handle_get_league_settings({})

        response = json.loads(result)
        assert response["success"] is True

        # Verify ESPNClient was called with default values from config
        mock_client_class.assert_called_once()
        call_args = mock_client_class.call_args[1]
        assert call_args["league_id"] == "123456"

    @pytest.mark.asyncio
    @patch('espn_fantasy_mcp.tools.league_tools.ESPNClient')
    async def test_handle_get_league_settings_error(self, mock_client_class, mock_env_vars):
        """Test handle_get_league_settings with error."""
        # Mock the client instance and make the method raise an exception
        mock_client = Mock()
        mock_client.get_league_settings.side_effect = ConnectionError("API connection failed")
        mock_client_class.return_value = mock_client

        result = await league_tools.handle_get_league_settings({
            "league_id": "123456"
        })

        response = json.loads(result)
        assert response["success"] is False
        assert response["error"] == "ConnectionError"
        assert "API connection failed" in response["message"]

    @pytest.mark.asyncio
    @patch('espn_fantasy_mcp.tools.league_tools.ESPNClient')
    async def test_handle_get_standings_success(self, mock_client_class, mock_env_vars):
        """Test handle_get_standings with successful response."""
        mock_client = Mock()
        mock_teams = [
            Team(
                team_id=0,
                team_name="Team A",
                team_abbrev="TMA",
                owners=["Owner A"],
                primary_owner="Owner A",
                wins=15,
                losses=5,
                standing=1
            ),
            Team(
                team_id=1,
                team_name="Team B",
                team_abbrev="TMB",
                owners=["Owner B"],
                primary_owner="Owner B",
                wins=10,
                losses=10,
                standing=2
            ),
        ]
        mock_client.get_standings.return_value = mock_teams
        mock_client_class.return_value = mock_client

        result = await league_tools.handle_get_standings({
            "league_id": "123456",
            "season_year": 2024
        })

        response = json.loads(result)
        assert response["success"] is True
        assert len(response["data"]) == 2
        assert response["data"][0]["team_name"] == "Team A"
        assert response["data"][0]["standing"] == 1

    @pytest.mark.asyncio
    async def test_handle_get_standings_missing_league_id(self, monkeypatch):
        """Test handle_get_standings without league_id."""
        monkeypatch.delenv("ESPN_LEAGUE_ID", raising=False)

        import importlib
        import espn_fantasy_mcp.config
        importlib.reload(espn_fantasy_mcp.config)

        with pytest.raises(ValueError, match="league_id is required"):
            await league_tools.handle_get_standings({})

    @pytest.mark.asyncio
    @patch('espn_fantasy_mcp.tools.league_tools.Config')
    @patch('espn_fantasy_mcp.tools.league_tools.ESPNClient')
    async def test_handle_get_standings_uses_defaults(self, mock_client_class, mock_config):
        """Test handle_get_standings uses default values from config."""
        # Mock Config methods
        mock_config.get_default_league_id.return_value = "123456"
        mock_config.get_default_season_year.return_value = 2024
        mock_config.ESPN_S2 = "test_s2"
        mock_config.ESPN_SWID = "{TEST-SWID}"

        mock_client = Mock()
        mock_client.get_standings.return_value = []
        mock_client_class.return_value = mock_client

        # Call without explicit league_id or season_year
        result = await league_tools.handle_get_standings({})

        response = json.loads(result)
        assert response["success"] is True

        # Verify ESPNClient was called with default values from config
        mock_client_class.assert_called_once()
        call_args = mock_client_class.call_args[1]
        assert call_args["league_id"] == "123456"

    @pytest.mark.asyncio
    @patch('espn_fantasy_mcp.tools.league_tools.ESPNClient')
    async def test_handle_get_standings_empty(self, mock_client_class, mock_env_vars):
        """Test handle_get_standings with no teams."""
        mock_client = Mock()
        mock_client.get_standings.return_value = []
        mock_client_class.return_value = mock_client

        result = await league_tools.handle_get_standings({
            "league_id": "123456"
        })

        response = json.loads(result)
        assert response["success"] is True
        assert response["data"] == []

    @pytest.mark.asyncio
    @patch('espn_fantasy_mcp.tools.league_tools.ESPNClient')
    async def test_handle_get_standings_error(self, mock_client_class, mock_env_vars):
        """Test handle_get_standings with error."""
        # Mock the client instance and make the method raise an exception
        mock_client = Mock()
        mock_client.get_standings.side_effect = ValueError("Invalid league ID")
        mock_client_class.return_value = mock_client

        result = await league_tools.handle_get_standings({
            "league_id": "invalid"
        })

        response = json.loads(result)
        assert response["success"] is False
        assert response["error"] == "ValueError"
        assert "Invalid league ID" in response["message"]
