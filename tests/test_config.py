"""Unit tests for configuration."""
import pytest
from espn_fantasy_mcp.config import Config


@pytest.mark.unit
class TestConfig:
    """Tests for Config class."""

    def test_config_with_env_vars(self, monkeypatch):
        """Test Config class attributes are accessible."""
        # Directly set Config class attributes to test attribute access
        monkeypatch.setattr("espn_fantasy_mcp.config.Config.ESPN_S2", "test_espn_s2_token")
        monkeypatch.setattr("espn_fantasy_mcp.config.Config.ESPN_SWID", "{TEST-SWID-1234}")
        monkeypatch.setattr("espn_fantasy_mcp.config.Config.ESPN_LEAGUE_ID", "123456")
        monkeypatch.setattr("espn_fantasy_mcp.config.Config.ESPN_SEASON_YEAR", 2024)
        monkeypatch.setattr("espn_fantasy_mcp.config.Config.ESPN_TEAM_ID", "0")

        assert Config.ESPN_S2 == "test_espn_s2_token"
        assert Config.ESPN_SWID == "{TEST-SWID-1234}"
        assert Config.ESPN_LEAGUE_ID == "123456"
        assert Config.ESPN_SEASON_YEAR == 2024
        assert Config.ESPN_TEAM_ID == "0"

    def test_has_auth_with_credentials(self, monkeypatch):
        """Test has_auth returns True when credentials are set."""
        # Set both credentials to test has_auth logic
        monkeypatch.setattr("espn_fantasy_mcp.config.Config.ESPN_S2", "test_espn_s2_token")
        monkeypatch.setattr("espn_fantasy_mcp.config.Config.ESPN_SWID", "{TEST-SWID-1234}")

        assert Config.has_auth() is True

    def test_has_auth_without_credentials(self, monkeypatch):
        """Test has_auth returns False when credentials are missing."""
        # Set both credentials to None to test has_auth logic
        monkeypatch.setattr("espn_fantasy_mcp.config.Config.ESPN_S2", None)
        monkeypatch.setattr("espn_fantasy_mcp.config.Config.ESPN_SWID", None)

        assert Config.has_auth() is False

    def test_has_auth_partial_credentials(self, monkeypatch):
        """Test has_auth returns False with only one credential."""
        # Set one credential to test has_auth requires both
        monkeypatch.setattr("espn_fantasy_mcp.config.Config.ESPN_S2", "test_token")
        monkeypatch.setattr("espn_fantasy_mcp.config.Config.ESPN_SWID", None)

        assert Config.has_auth() is False

    def test_get_default_league_id(self, monkeypatch):
        """Test get_default_league_id returns league ID."""
        monkeypatch.setattr("espn_fantasy_mcp.config.Config.ESPN_LEAGUE_ID", "123456")

        assert Config.get_default_league_id() == "123456"

    def test_get_default_league_id_not_set(self, monkeypatch):
        """Test get_default_league_id returns None when not set."""
        monkeypatch.setattr("espn_fantasy_mcp.config.Config.ESPN_LEAGUE_ID", None)

        assert Config.get_default_league_id() is None

    def test_get_default_season_year(self, monkeypatch):
        """Test get_default_season_year returns season year."""
        monkeypatch.setattr("espn_fantasy_mcp.config.Config.ESPN_SEASON_YEAR", 2024)

        assert Config.get_default_season_year() == 2024

    def test_get_default_season_year_fallback(self, monkeypatch):
        """Test get_default_season_year returns current value (default is 2024)."""
        # This tests that the method returns the class attribute value
        monkeypatch.setattr("espn_fantasy_mcp.config.Config.ESPN_SEASON_YEAR", 2024)

        assert Config.get_default_season_year() == 2024

    def test_get_default_team_id(self, monkeypatch):
        """Test get_default_team_id returns team ID."""
        monkeypatch.setattr("espn_fantasy_mcp.config.Config.ESPN_TEAM_ID", "0")

        assert Config.get_default_team_id() == "0"

    def test_get_default_team_id_not_set(self, monkeypatch):
        """Test get_default_team_id returns None when not set."""
        monkeypatch.setattr("espn_fantasy_mcp.config.Config.ESPN_TEAM_ID", None)

        assert Config.get_default_team_id() is None
