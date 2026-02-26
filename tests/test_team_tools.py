"""Tests for team tools."""
import pytest
import json
from unittest.mock import patch, Mock
from espn_fantasy_mcp.tools import team_tools
from espn_fantasy_mcp.models import Team, Player, RosterStatus


@pytest.mark.unit
class TestTeamTools:
    """Tests for team tool functions."""

    def test_get_tools(self):
        """Test that get_tools returns correct tool definitions."""
        tools = team_tools.get_tools()

        assert len(tools) == 2
        assert tools[0].name == "get_team"
        assert tools[1].name == "get_roster"

    @pytest.mark.asyncio
    async def test_handle_tool_unknown(self):
        """Test handle_tool with unknown tool name."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await team_tools.handle_tool("unknown_tool", {})

    @pytest.mark.asyncio
    @patch('espn_fantasy_mcp.tools.team_tools.ESPNClient')
    async def test_handle_get_team_success(self, mock_client_class, mock_env_vars):
        """Test handle_get_team with successful response."""
        mock_client = Mock()
        mock_team = Team(
            team_id=0,
            team_name="Test Team",
            team_abbrev="TEST",
            owners=["Owner 1"],
            primary_owner="Owner 1",
            wins=10,
            losses=5,
            standing=1
        )
        mock_client.get_team.return_value = mock_team
        mock_client_class.return_value = mock_client

        result = await team_tools.handle_get_team({
            "league_id": "123456",
            "team_id": 0,
            "season_year": 2024
        })

        response = json.loads(result)
        assert response["success"] is True
        assert response["data"]["team_name"] == "Test Team"
        assert response["data"]["wins"] == 10

    @pytest.mark.asyncio
    async def test_handle_get_team_missing_team_id(self, mock_env_vars):
        """Test handle_get_team without team_id."""
        with pytest.raises(ValueError, match="team_id is required"):
            await team_tools.handle_get_team({
                "league_id": "123456"
            })

    @pytest.mark.asyncio
    async def test_handle_get_team_missing_league_id(self, monkeypatch):
        """Test handle_get_team without league_id."""
        monkeypatch.delenv("ESPN_LEAGUE_ID", raising=False)

        import importlib
        import espn_fantasy_mcp.config
        importlib.reload(espn_fantasy_mcp.config)

        with pytest.raises(ValueError, match="league_id is required"):
            await team_tools.handle_get_team({
                "team_id": 0
            })

    @pytest.mark.asyncio
    @patch('espn_fantasy_mcp.tools.team_tools.ESPNClient')
    async def test_handle_get_team_invalid_team_id(self, mock_client_class, mock_env_vars):
        """Test handle_get_team with invalid team_id."""
        mock_client = Mock()
        mock_client.get_team.side_effect = IndexError("Team index out of range")
        mock_client_class.return_value = mock_client

        result = await team_tools.handle_get_team({
            "league_id": "123456",
            "team_id": 99
        })

        response = json.loads(result)
        assert response["success"] is False
        assert response["error"] == "IndexError"

    @pytest.mark.asyncio
    @patch('espn_fantasy_mcp.tools.team_tools.ESPNClient')
    async def test_handle_get_roster_success(self, mock_client_class, mock_env_vars):
        """Test handle_get_roster with successful response."""
        mock_client = Mock()
        mock_player = Player(
            player_id=12345,
            name="Test Player",
            team="NYY",
            position="SS",
            roster_status=RosterStatus.ROSTERED,
            fantasy_team_id=0
        )
        mock_client.get_roster.return_value = [mock_player]
        mock_client_class.return_value = mock_client

        result = await team_tools.handle_get_roster({
            "league_id": "123456",
            "team_id": 0
        })

        response = json.loads(result)
        assert response["success"] is True
        assert len(response["data"]) == 1
        assert response["data"][0]["name"] == "Test Player"

    @pytest.mark.asyncio
    async def test_handle_get_roster_missing_team_id(self, mock_env_vars):
        """Test handle_get_roster without team_id."""
        with pytest.raises(ValueError, match="team_id is required"):
            await team_tools.handle_get_roster({
                "league_id": "123456"
            })

    @pytest.mark.asyncio
    async def test_handle_get_roster_missing_league_id(self, monkeypatch):
        """Test handle_get_roster without league_id."""
        monkeypatch.delenv("ESPN_LEAGUE_ID", raising=False)

        import importlib
        import espn_fantasy_mcp.config
        importlib.reload(espn_fantasy_mcp.config)

        with pytest.raises(ValueError, match="league_id is required"):
            await team_tools.handle_get_roster({
                "team_id": 0
            })

    @pytest.mark.asyncio
    @patch('espn_fantasy_mcp.tools.team_tools.ESPNClient')
    async def test_handle_get_roster_empty(self, mock_client_class, mock_env_vars):
        """Test handle_get_roster with empty roster."""
        mock_client = Mock()
        mock_client.get_roster.return_value = []
        mock_client_class.return_value = mock_client

        result = await team_tools.handle_get_roster({
            "league_id": "123456",
            "team_id": 0
        })

        response = json.loads(result)
        assert response["success"] is True
        assert response["data"] == []

    @pytest.mark.asyncio
    @patch('espn_fantasy_mcp.tools.team_tools.ESPNClient')
    async def test_handle_get_roster_error(self, mock_client_class, mock_env_vars):
        """Test handle_get_roster with error."""
        # Mock the client instance and make the method raise an exception
        mock_client = Mock()
        mock_client.get_roster.side_effect = ConnectionError("API connection failed")
        mock_client_class.return_value = mock_client

        result = await team_tools.handle_get_roster({
            "league_id": "123456",
            "team_id": 0
        })

        response = json.loads(result)
        assert response["success"] is False
        assert response["error"] == "ConnectionError"
