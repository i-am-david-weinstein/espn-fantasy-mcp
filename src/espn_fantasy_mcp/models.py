"""Data models for ESPN Fantasy Baseball."""
from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import List, Dict, Optional, Any


class RosterStatus(str, Enum):
    """Player roster status in fantasy league."""
    ROSTERED = "ROSTERED"
    FREE_AGENT = "FREE_AGENT"
    WAIVERS = "WAIVERS"
    UNKNOWN = "UNKNOWN"


@dataclass
class Team:
    """Represents a fantasy baseball team."""

    team_id: int
    team_name: str
    team_abbrev: str
    owners: List[str]
    primary_owner: str
    wins: int
    losses: int
    ties: int = 0
    points_for: float = 0.0
    points_against: float = 0.0
    standing: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Player:
    """Represents a fantasy baseball player."""

    player_id: int
    name: str
    team: str  # MLB team abbreviation
    position: str
    eligible_slots: List[str] = field(default_factory=list)
    lineup_slot: Optional[str] = None
    injury_status: str = "ACTIVE"
    stats: Dict[str, Any] = field(default_factory=dict)

    # Fantasy team ownership information
    roster_status: RosterStatus = RosterStatus.UNKNOWN
    fantasy_team_id: Optional[int] = None
    fantasy_team_name: Optional[str] = None
    fantasy_team_abbrev: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class LeagueSettings:
    """Represents league configuration and settings.

    Exposes all settings from ESPN API response.
    Complex configuration objects are provided as dictionaries.
    """

    league_id: str
    name: str
    season_year: int
    team_count: int
    playoff_team_count: int
    reg_season_count: int
    scoring_type: str

    # Detailed settings from ESPN API (as raw dicts)
    acquisition_settings: Dict[str, Any] = field(default_factory=dict)
    draft_settings: Dict[str, Any] = field(default_factory=dict)
    finance_settings: Dict[str, Any] = field(default_factory=dict)
    roster_settings: Dict[str, Any] = field(default_factory=dict)
    schedule_settings: Dict[str, Any] = field(default_factory=dict)
    scoring_settings: Dict[str, Any] = field(default_factory=dict)
    trade_settings: Dict[str, Any] = field(default_factory=dict)

    # Simple settings fields
    experience_type: Optional[str] = None
    is_public: bool = True
    restriction_type: Optional[str] = None

    # Computed/helper fields
    stat_categories: Dict[str, List[str]] = field(default_factory=dict)  # Actual scoring categories used by this league
    stat_id_map: Dict[str, str] = field(default_factory=dict)  # Map of stat IDs to readable names (from STATS_MAP)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)
