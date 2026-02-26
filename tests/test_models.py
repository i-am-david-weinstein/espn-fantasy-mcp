"""Unit tests for data models."""
import pytest
from espn_fantasy_mcp.models import Team, Player, LeagueSettings, RosterStatus


@pytest.mark.unit
class TestRosterStatus:
    """Tests for RosterStatus enum."""

    def test_roster_status_values(self):
        """Test that RosterStatus has expected values."""
        assert RosterStatus.ROSTERED == "ROSTERED"
        assert RosterStatus.FREE_AGENT == "FREE_AGENT"
        assert RosterStatus.WAIVERS == "WAIVERS"
        assert RosterStatus.UNKNOWN == "UNKNOWN"


@pytest.mark.unit
class TestTeam:
    """Tests for Team model."""

    def test_team_creation(self):
        """Test creating a Team instance."""
        team = Team(
            team_id=1,
            team_name="Test Team",
            team_abbrev="TEST",
            owners=["Owner 1", "Owner 2"],
            primary_owner="Owner 1",
            wins=10,
            losses=5,
            ties=0,
            points_for=500.0,
            points_against=450.0,
            standing=1
        )

        assert team.team_id == 1
        assert team.team_name == "Test Team"
        assert team.team_abbrev == "TEST"
        assert len(team.owners) == 2
        assert team.primary_owner == "Owner 1"
        assert team.wins == 10
        assert team.losses == 5

    def test_team_defaults(self):
        """Test Team default values."""
        team = Team(
            team_id=1,
            team_name="Test Team",
            team_abbrev="TEST",
            owners=["Owner 1"],
            primary_owner="Owner 1",
            wins=10,
            losses=5
        )

        assert team.ties == 0
        assert team.points_for == 0.0
        assert team.points_against == 0.0
        assert team.standing == 0

    def test_team_to_dict(self, sample_team_data):
        """Test Team.to_dict() method."""
        team = Team(**sample_team_data)
        team_dict = team.to_dict()

        assert isinstance(team_dict, dict)
        assert team_dict["team_id"] == sample_team_data["team_id"]
        assert team_dict["team_name"] == sample_team_data["team_name"]
        assert team_dict["wins"] == sample_team_data["wins"]


@pytest.mark.unit
class TestPlayer:
    """Tests for Player model."""

    def test_player_creation(self):
        """Test creating a Player instance."""
        player = Player(
            player_id=12345,
            name="Test Player",
            team="NYY",
            position="SS",
            eligible_slots=["SS", "2B", "UTIL"],
            lineup_slot="SS",
            injury_status="ACTIVE"
        )

        assert player.player_id == 12345
        assert player.name == "Test Player"
        assert player.team == "NYY"
        assert player.position == "SS"
        assert "SS" in player.eligible_slots

    def test_player_defaults(self):
        """Test Player default values."""
        player = Player(
            player_id=12345,
            name="Test Player",
            team="NYY",
            position="SS"
        )

        assert player.eligible_slots == []
        assert player.lineup_slot is None
        assert player.injury_status == "ACTIVE"
        assert player.stats == {}
        assert player.roster_status == RosterStatus.UNKNOWN
        assert player.fantasy_team_id is None

    def test_player_with_fantasy_team_info(self):
        """Test Player with fantasy team ownership information."""
        player = Player(
            player_id=12345,
            name="Test Player",
            team="NYY",
            position="SS",
            roster_status=RosterStatus.ROSTERED,
            fantasy_team_id=0,
            fantasy_team_name="Test Team",
            fantasy_team_abbrev="TEST"
        )

        assert player.roster_status == RosterStatus.ROSTERED
        assert player.fantasy_team_id == 0
        assert player.fantasy_team_name == "Test Team"

    def test_player_to_dict(self, sample_player_data):
        """Test Player.to_dict() method."""
        player = Player(**sample_player_data)
        player_dict = player.to_dict()

        assert isinstance(player_dict, dict)
        assert player_dict["player_id"] == sample_player_data["player_id"]
        assert player_dict["name"] == sample_player_data["name"]
        assert player_dict["roster_status"] == sample_player_data["roster_status"]


@pytest.mark.unit
class TestLeagueSettings:
    """Tests for LeagueSettings model."""

    def test_league_settings_creation(self):
        """Test creating a LeagueSettings instance."""
        settings = LeagueSettings(
            league_id="123456",
            name="Test League",
            season_year=2024,
            team_count=12,
            playoff_team_count=6,
            reg_season_count=162,
            scoring_type="H2H_CATEGORY"
        )

        assert settings.league_id == "123456"
        assert settings.name == "Test League"
        assert settings.season_year == 2024
        assert settings.team_count == 12
        assert settings.scoring_type == "H2H_CATEGORY"

    def test_league_settings_defaults(self):
        """Test LeagueSettings default values."""
        settings = LeagueSettings(
            league_id="123456",
            name="Test League",
            season_year=2024,
            team_count=12,
            playoff_team_count=6,
            reg_season_count=162,
            scoring_type="H2H_CATEGORY"
        )

        assert settings.acquisition_settings == {}
        assert settings.draft_settings == {}
        assert settings.finance_settings == {}
        assert settings.roster_settings == {}
        assert settings.is_public is True
        assert settings.stat_categories == {}

    def test_league_settings_with_detailed_config(self, sample_league_settings):
        """Test LeagueSettings with detailed configuration."""
        settings = LeagueSettings(**sample_league_settings)

        assert settings.acquisition_settings["acquisitionBudget"] == 100
        assert settings.draft_settings["type"] == "SNAKE"
        assert "C" in settings.roster_settings["lineupSlotCounts"]
        assert "batting" in settings.stat_categories

    def test_league_settings_to_dict(self, sample_league_settings):
        """Test LeagueSettings.to_dict() method."""
        settings = LeagueSettings(**sample_league_settings)
        settings_dict = settings.to_dict()

        assert isinstance(settings_dict, dict)
        assert settings_dict["league_id"] == sample_league_settings["league_id"]
        assert settings_dict["name"] == sample_league_settings["name"]
        assert settings_dict["team_count"] == sample_league_settings["team_count"]
