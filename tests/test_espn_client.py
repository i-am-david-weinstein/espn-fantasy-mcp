"""Unit tests for ESPN client."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from espn_fantasy_mcp.espn_client import ESPNClient
from espn_fantasy_mcp.models import RosterStatus


@pytest.mark.unit
class TestESPNClient:
    """Tests for ESPNClient class."""

    @patch('espn_fantasy_mcp.espn_client.League')
    def test_client_initialization(self, mock_league_class, mock_env_vars):
        """Test ESPNClient initialization."""
        mock_league = Mock()
        mock_league_class.return_value = mock_league

        client = ESPNClient(
            league_id="123456",
            season_year=2024,
            espn_s2="test_s2",
            swid="{TEST-SWID}"
        )

        assert client.league_id == 123456
        assert client.season_year == 2024
        assert client.espn_s2 == "test_s2"
        assert client.swid == "{TEST-SWID}"
        mock_league_class.assert_called_once()

    @patch('espn_fantasy_mcp.espn_client.League')
    def test_get_team(self, mock_league_class, mock_espn_team):
        """Test getting a team."""
        mock_league = Mock()
        mock_league.teams = [mock_espn_team]
        mock_league_class.return_value = mock_league

        client = ESPNClient(league_id="123456")
        team = client.get_team(0)

        assert team.team_id == 0
        assert team.team_name == "Test Team"
        assert team.team_abbrev == "TEST"
        assert team.wins == 10
        assert team.losses == 5

    @patch('espn_fantasy_mcp.espn_client.League')
    def test_get_standings(self, mock_league_class, mock_espn_team):
        """Test getting league standings."""
        mock_team_1 = Mock()
        mock_team_1.team_name = "Team A"
        mock_team_1.team_abbrev = "TMA"
        mock_team_1.owners = ["Owner A"]
        mock_team_1.wins = 15
        mock_team_1.losses = 5
        mock_team_1.standing = 1

        mock_team_2 = Mock()
        mock_team_2.team_name = "Team B"
        mock_team_2.team_abbrev = "TMB"
        mock_team_2.owners = ["Owner B"]
        mock_team_2.wins = 10
        mock_team_2.losses = 10
        mock_team_2.standing = 2

        mock_league = Mock()
        mock_league.teams = [mock_team_1, mock_team_2]
        mock_league_class.return_value = mock_league

        client = ESPNClient(league_id="123456")
        standings = client.get_standings()

        assert len(standings) == 2
        assert standings[0].team_name == "Team A"
        assert standings[0].standing == 1
        assert standings[1].team_name == "Team B"
        assert standings[1].standing == 2

    @patch('espn_fantasy_mcp.espn_client.League')
    def test_get_roster(self, mock_league_class, mock_espn_team, mock_espn_player):
        """Test getting a team roster."""
        mock_espn_team.roster = [mock_espn_player]

        mock_league = Mock()
        mock_league.teams = [mock_espn_team]
        mock_league_class.return_value = mock_league

        client = ESPNClient(league_id="123456")
        roster = client.get_roster(0)

        assert len(roster) == 1
        assert roster[0].name == "Test Player"
        assert roster[0].roster_status == RosterStatus.ROSTERED
        assert roster[0].fantasy_team_id == 0
        assert roster[0].fantasy_team_name == "Test Team"

    @patch('espn_fantasy_mcp.espn_client.League')
    def test_get_free_agents(self, mock_league_class, mock_espn_player):
        """Test getting free agents."""
        # Create a free agent player (not rostered)
        fa_player = Mock()
        fa_player.playerId = 99999
        fa_player.name = "Free Agent Player"
        fa_player.proTeam = "BOS"
        fa_player.position = "OF"
        fa_player.eligibleSlots = ["OF"]
        fa_player.injuryStatus = "ACTIVE"
        fa_player.stats = {}
        fa_player.acquisitionType = "FREE_AGENT"

        mock_league = Mock()
        mock_league.free_agents = Mock(return_value=[fa_player])
        mock_league_class.return_value = mock_league

        client = ESPNClient(league_id="123456")
        free_agents = client.get_free_agents(size=50)

        assert len(free_agents) == 1
        assert free_agents[0].name == "Free Agent Player"
        assert free_agents[0].roster_status == RosterStatus.FREE_AGENT
        assert free_agents[0].fantasy_team_id is None

    @patch('espn_fantasy_mcp.espn_client.League')
    def test_get_free_agents_with_position_filter(self, mock_league_class):
        """Test getting free agents with position filter."""
        mock_league = Mock()
        mock_league.free_agents = Mock(return_value=[])
        mock_league_class.return_value = mock_league

        client = ESPNClient(league_id="123456")
        client.get_free_agents(size=20, position="SS")

        mock_league.free_agents.assert_called_once_with(size=20, position="SS")

    @patch('espn_fantasy_mcp.espn_client.League')
    def test_get_player_by_name_exact_match(self, mock_league_class, mock_espn_player):
        """Test getting a player by exact name match."""
        mock_league = Mock()
        mock_league.player_map = {"Test Player": 12345, 12345: "Test Player"}
        mock_league.teams = []

        # Mock free_agents to return our player
        mock_league.free_agents = Mock(return_value=[mock_espn_player])
        mock_league_class.return_value = mock_league

        client = ESPNClient(league_id="123456")
        player, suggestions = client.get_player_by_name("Test Player")

        assert player is not None
        assert player.name == "Test Player"
        assert len(suggestions) == 0

    @patch('espn_fantasy_mcp.espn_client.League')
    def test_get_player_by_name_fuzzy_match(self, mock_league_class):
        """Test getting a player by fuzzy name match.

        Uses a typo "Aaron Jdge" (missing 'u') to test fuzzy matching.
        The implementation uses rapidfuzz.process.extract() with WRatio scorer,
        which should reliably match this typo to "Aaron Judge" with >90% similarity.
        """
        mock_league = Mock()
        mock_league.player_map = {
            "Aaron Judge": 30836,
            "Mike Trout": 31000,
            "Shohei Ohtani": 39572,
            30836: "Aaron Judge",
            31000: "Mike Trout",
            39572: "Shohei Ohtani"
        }
        mock_league_class.return_value = mock_league

        client = ESPNClient(league_id="123456")
        # Use a typo to test fuzzy matching
        player, suggestions = client.get_player_by_name("Aaron Jdge", fuzzy_threshold=85)

        # Should not find exact match
        assert player is None

        # Fuzzy matching should provide suggestions
        # The typo "Aaron Jdge" is very similar to "Aaron Judge" and should match
        assert len(suggestions) > 0, "Fuzzy matching should provide suggestions for close typos"
        assert "Aaron Judge" in suggestions, (
            "Expected 'Aaron Judge' in suggestions for typo 'Aaron Jdge'. "
            f"Got suggestions: {suggestions}"
        )

    @patch('espn_fantasy_mcp.espn_client.League')
    def test_get_player_by_name_no_match(self, mock_league_class):
        """Test getting a player with no match.

        Tests that completely dissimilar names don't produce suggestions
        when using a high fuzzy threshold.
        """
        mock_league = Mock()
        mock_league.player_map = {"Aaron Judge": 30836, 30836: "Aaron Judge"}
        mock_league_class.return_value = mock_league

        client = ESPNClient(league_id="123456")
        # "Nonexistent Player" should not match "Aaron Judge" at 90% threshold
        player, suggestions = client.get_player_by_name("Nonexistent Player", fuzzy_threshold=90)

        assert player is None
        # Should not suggest "Aaron Judge" for "Nonexistent Player"
        # These strings have low similarity and shouldn't meet the 90% threshold
        assert "Aaron Judge" not in suggestions, (
            "Should not suggest 'Aaron Judge' for completely different name 'Nonexistent Player'"
        )

    @patch('espn_fantasy_mcp.espn_client.League')
    def test_get_player_by_name_fuzzy_disabled(self, mock_league_class):
        """Test getting a player with fuzzy matching disabled.

        Verifies that when fuzzy_match=False, no suggestions are returned
        even for close typos.
        """
        mock_league = Mock()
        mock_league.player_map = {
            "Aaron Judge": 30836,
            30836: "Aaron Judge"
        }
        mock_league_class.return_value = mock_league

        client = ESPNClient(league_id="123456")
        # Disable fuzzy matching
        player, suggestions = client.get_player_by_name("Aaron Jdge", fuzzy_match=False)

        assert player is None
        # With fuzzy matching disabled, should not provide any suggestions
        assert len(suggestions) == 0, (
            "Should not provide suggestions when fuzzy_match=False"
        )
