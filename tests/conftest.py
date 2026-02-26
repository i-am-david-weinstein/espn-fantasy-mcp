"""Shared pytest fixtures for ESPN Fantasy MCP tests."""
import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any


@pytest.fixture
def mock_espn_league() -> Mock:
    """Mock ESPN League object."""
    league = Mock()
    league.league_id = 123456
    league.year = 2024
    league.settings = Mock()
    league.settings.name = "Test League"
    league.settings.team_count = 12
    league.settings.playoff_team_count = 6
    league.settings.reg_season_count = 162
    league.settings.scoring_type = "H2H_CATEGORY"
    return league


@pytest.fixture
def mock_espn_team() -> Mock:
    """Mock ESPN Team object."""
    team = Mock()
    team.team_id = 0
    team.team_name = "Test Team"
    team.team_abbrev = "TEST"
    team.owners = [{"firstName": "John", "lastName": "Doe"}]
    team.wins = 10
    team.losses = 5
    team.ties = 0
    team.points_for = 500.0
    team.points_against = 450.0
    team.standing = 1
    return team


@pytest.fixture
def mock_espn_player() -> Mock:
    """Mock ESPN Player object."""
    player = Mock()
    player.playerId = 12345
    player.name = "Test Player"
    player.proTeam = "NYY"
    player.position = "SS"
    player.eligibleSlots = ["SS", "2B", "UTIL"]
    player.lineupSlot = "SS"
    player.injuryStatus = "ACTIVE"
    player.stats = {}
    return player


@pytest.fixture
def sample_league_settings() -> Dict[str, Any]:
    """Sample league settings data."""
    return {
        "league_id": "123456",
        "name": "Test Fantasy League",
        "season_year": 2024,
        "team_count": 12,
        "playoff_team_count": 6,
        "reg_season_count": 162,
        "scoring_type": "H2H_CATEGORY",
        "acquisition_settings": {
            "acquisitionBudget": 100,
            "acquisitionLimit": -1,
            "isWaiverOrderReset": False
        },
        "draft_settings": {
            "date": 1710000000000,
            "type": "SNAKE"
        },
        "roster_settings": {
            "lineupSlotCounts": {
                "C": 1,
                "1B": 1,
                "2B": 1,
                "SS": 1,
                "3B": 1,
                "OF": 3,
                "UTIL": 1,
                "SP": 2,
                "RP": 2,
                "P": 2,
                "BE": 5
            }
        },
        "scoring_settings": {},
        "stat_categories": {
            "batting": ["R", "HR", "RBI", "SB", "AVG", "OPS"],
            "pitching": ["W", "SV", "K", "ERA", "WHIP", "QS"]
        },
        "stat_id_map": {}
    }


@pytest.fixture
def sample_player_data() -> Dict[str, Any]:
    """Sample player data."""
    return {
        "player_id": 12345,
        "name": "Aaron Judge",
        "team": "NYY",
        "position": "OF",
        "eligible_slots": ["OF", "UTIL"],
        "lineup_slot": "OF",
        "injury_status": "ACTIVE",
        "stats": {
            "2024": {
                "AB": 500,
                "R": 100,
                "HR": 45,
                "RBI": 120,
                "SB": 10,
                "AVG": 0.300
            }
        },
        "roster_status": "ROSTERED",
        "fantasy_team_id": 0,
        "fantasy_team_name": "Test Team",
        "fantasy_team_abbrev": "TEST"
    }


@pytest.fixture
def sample_team_data() -> Dict[str, Any]:
    """Sample team data."""
    return {
        "team_id": 0,
        "team_name": "Test Team",
        "team_abbrev": "TEST",
        "owners": ["John Doe"],
        "primary_owner": "John Doe",
        "wins": 10,
        "losses": 5,
        "ties": 0,
        "points_for": 500.0,
        "points_against": 450.0,
        "standing": 1
    }


@pytest.fixture(autouse=True)
def clear_player_map_cache() -> None:
    """Clear the ESPNClient module-level player map cache before each test.

    Prevents test pollution where one test's cached player_map leaks into
    subsequent tests that use the same league_id + season_year cache key.
    """
    from espn_fantasy_mcp import espn_client
    espn_client._player_map_cache.clear()


@pytest.fixture
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock environment variables for testing."""
    monkeypatch.setenv("ESPN_S2", "test_espn_s2_token")
    monkeypatch.setenv("ESPN_SWID", "{TEST-SWID-1234}")
    monkeypatch.setenv("ESPN_LEAGUE_ID", "123456")
    monkeypatch.setenv("ESPN_SEASON_YEAR", "2024")
    monkeypatch.setenv("ESPN_TEAM_ID", "0")


@pytest.fixture
def mock_player():
    """Factory fixture for creating mock objects representing our Player model.

    Returns a factory function so tests can create multiple players with
    different attributes. Uses snake_case attributes to match our Player
    dataclass, unlike mock_espn_player which uses the raw ESPN API camelCase.

    Usage:
        def test_something(mock_player):
            player = mock_player(player_id=111, lineup_slot="BE")
    """
    def _make(
        player_id: int = 12345,
        name: str = "Test Player",
        lineup_slot: str = "BE",
        position: str = "OF",
    ) -> Mock:
        player = Mock()
        player.player_id = player_id
        player.name = name
        player.lineup_slot = lineup_slot
        player.position = position
        return player
    return _make


@pytest.fixture
def mock_espn_client() -> Mock:
    """Mock ESPNClient instance with sensible defaults."""
    client = Mock()
    client.league.currentMatchupPeriod = 5
    client.get_team.return_value = Mock(team_name="Test Team")
    client.modify_lineup.return_value = {
        "id": "txn-abc123",
        "status": "EXECUTED",
        "scoringPeriodId": 5,
    }
    return client
