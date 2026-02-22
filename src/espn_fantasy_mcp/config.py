"""Configuration management for ESPN Fantasy MCP server."""
import os
from typing import Optional
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()


class Config:
    """ESPN Fantasy MCP Server configuration."""

    # ESPN authentication (required for private leagues)
    ESPN_S2: Optional[str] = os.getenv("ESPN_S2")
    ESPN_SWID: Optional[str] = os.getenv("ESPN_SWID")

    # Optional defaults
    ESPN_LEAGUE_ID: Optional[str] = os.getenv("ESPN_LEAGUE_ID")
    ESPN_SEASON_YEAR: int = int(os.getenv("ESPN_SEASON_YEAR", "2024"))
    ESPN_TEAM_ID: Optional[str] = os.getenv("ESPN_TEAM_ID")

    @classmethod
    def has_auth(cls) -> bool:
        """Check if ESPN authentication credentials are available."""
        return bool(cls.ESPN_S2 and cls.ESPN_SWID)

    @classmethod
    def get_default_league_id(cls) -> Optional[str]:
        """Get default league ID if set."""
        return cls.ESPN_LEAGUE_ID

    @classmethod
    def get_default_season_year(cls) -> int:
        """Get default season year."""
        return cls.ESPN_SEASON_YEAR

    @classmethod
    def get_default_team_id(cls) -> Optional[str]:
        """Get default team ID if set."""
        return cls.ESPN_TEAM_ID
