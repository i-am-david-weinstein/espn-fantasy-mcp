"""Unit tests for configuration."""
import pytest
from espn_fantasy_mcp.config import Config


@pytest.mark.unit
class TestConfig:
    """Tests for Config class."""

    def test_config_with_env_vars(self, mock_env_vars):
        """Test Config reads from environment variables."""
        # Need to reload the module to pick up new env vars
        import importlib
        import espn_fantasy_mcp.config
        importlib.reload(espn_fantasy_mcp.config)
        from espn_fantasy_mcp.config import Config

        assert Config.ESPN_S2 == "test_espn_s2_token"
        assert Config.ESPN_SWID == "{TEST-SWID-1234}"
        assert Config.ESPN_LEAGUE_ID == "123456"
        assert Config.ESPN_SEASON_YEAR == 2024
        assert Config.ESPN_TEAM_ID == "0"

    def test_has_auth_with_credentials(self, mock_env_vars):
        """Test has_auth returns True when credentials are set."""
        import importlib
        import espn_fantasy_mcp.config
        importlib.reload(espn_fantasy_mcp.config)
        from espn_fantasy_mcp.config import Config

        assert Config.has_auth() is True

    def test_has_auth_without_credentials(self, monkeypatch):
        """Test has_auth returns False when credentials are missing."""
        monkeypatch.delenv("ESPN_S2", raising=False)
        monkeypatch.delenv("ESPN_SWID", raising=False)

        import importlib
        import espn_fantasy_mcp.config
        importlib.reload(espn_fantasy_mcp.config)
        from espn_fantasy_mcp.config import Config

        assert Config.has_auth() is False

    def test_has_auth_partial_credentials(self, monkeypatch):
        """Test has_auth returns False with only one credential."""
        monkeypatch.setenv("ESPN_S2", "test_token")
        monkeypatch.delenv("ESPN_SWID", raising=False)

        import importlib
        import espn_fantasy_mcp.config
        importlib.reload(espn_fantasy_mcp.config)
        from espn_fantasy_mcp.config import Config

        assert Config.has_auth() is False

    def test_get_default_league_id(self, mock_env_vars):
        """Test get_default_league_id returns league ID."""
        import importlib
        import espn_fantasy_mcp.config
        importlib.reload(espn_fantasy_mcp.config)
        from espn_fantasy_mcp.config import Config

        assert Config.get_default_league_id() == "123456"

    def test_get_default_league_id_not_set(self, monkeypatch):
        """Test get_default_league_id returns None when not set."""
        monkeypatch.delenv("ESPN_LEAGUE_ID", raising=False)

        import importlib
        import espn_fantasy_mcp.config
        importlib.reload(espn_fantasy_mcp.config)
        from espn_fantasy_mcp.config import Config

        assert Config.get_default_league_id() is None

    def test_get_default_season_year(self, mock_env_vars):
        """Test get_default_season_year returns season year."""
        import importlib
        import espn_fantasy_mcp.config
        importlib.reload(espn_fantasy_mcp.config)
        from espn_fantasy_mcp.config import Config

        assert Config.get_default_season_year() == 2024

    def test_get_default_season_year_fallback(self, monkeypatch):
        """Test get_default_season_year falls back to 2024."""
        monkeypatch.delenv("ESPN_SEASON_YEAR", raising=False)

        import importlib
        import espn_fantasy_mcp.config
        importlib.reload(espn_fantasy_mcp.config)
        from espn_fantasy_mcp.config import Config

        assert Config.get_default_season_year() == 2024

    def test_get_default_team_id(self, mock_env_vars):
        """Test get_default_team_id returns team ID."""
        import importlib
        import espn_fantasy_mcp.config
        importlib.reload(espn_fantasy_mcp.config)
        from espn_fantasy_mcp.config import Config

        assert Config.get_default_team_id() == "0"

    def test_get_default_team_id_not_set(self, monkeypatch):
        """Test get_default_team_id returns None when not set."""
        monkeypatch.delenv("ESPN_TEAM_ID", raising=False)

        import importlib
        import espn_fantasy_mcp.config
        importlib.reload(espn_fantasy_mcp.config)
        from espn_fantasy_mcp.config import Config

        assert Config.get_default_team_id() is None
