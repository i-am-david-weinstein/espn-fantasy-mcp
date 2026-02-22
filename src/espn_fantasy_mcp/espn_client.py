"""ESPN Fantasy Baseball API client."""

from typing import Optional, List, Dict, Tuple
from rapidfuzz import process, fuzz
from espn_api.baseball import League
from espn_api.baseball.constant import STATS_MAP
from espn_fantasy_mcp.config import Config
from espn_fantasy_mcp.models import Team, Player, LeagueSettings, RosterStatus

# Module-level cache for player maps by league_id and year
_player_map_cache: Dict[Tuple[int, int], Dict] = {}


class ESPNClient:
    """Client for interacting with ESPN Fantasy Baseball API."""

    def __init__(
        self,
        league_id: str,
        season_year: Optional[int] = None,
        espn_s2: Optional[str] = None,
        swid: Optional[str] = None,
    ):
        """Initialize ESPN client.

        Args:
            league_id: ESPN league ID
            season_year: Season year (defaults to config)
            espn_s2: ESPN S2 cookie (defaults to config)
            swid: ESPN SWID cookie (defaults to config)
        """
        self.league_id = int(league_id)
        self.season_year = season_year or Config.get_default_season_year()
        self.espn_s2 = espn_s2 or Config.ESPN_S2
        self.swid = swid or Config.ESPN_SWID

        # Initialize league connection
        self.league = self._connect()

    def _connect(self) -> League:
        """Connect to ESPN Fantasy Baseball league.

        Returns:
            League object
        """
        return League(
            league_id=self.league_id,
            year=self.season_year,
            espn_s2=self.espn_s2,
            swid=self.swid,
        )

    def get_league_settings(self) -> LeagueSettings:
        """Get league settings and scoring categories.

        Returns:
            LeagueSettings object with league configuration
        """
        settings = self.league.settings

        # Fetch raw settings data from ESPN API
        raw_data = self.league.espn_request.get_league()
        raw_settings = raw_data.get('settings', {})

        # Build stat ID to name mapping from STATS_MAP
        stat_id_map = {str(stat_id): stat_name for stat_id, stat_name in STATS_MAP.items()}

        # Pitching stat names to identify them
        pitching_stat_names = {
            'GP', 'GS', 'OUTS', 'TBF', 'P_H', 'P_BB', 'WHIP', 'P_R', 'ER',
            'P_HR', 'ERA', 'K', 'W', 'L', 'SV', 'QS', 'HLD', 'BLSV', 'K/BB',
            'SVHD', 'WP', 'BLK', 'PK', 'SVO', 'CG', 'WPCT', 'OBA', 'OOBP',
            'P_IBB', 'SV%', '64'
        }

        # Parse actual scoring categories from scoringSettings.scoringItems
        batting_stats = []
        pitching_stats = []

        scoring_items = raw_settings.get('scoringSettings', {}).get('scoringItems', [])
        for item in scoring_items:
            stat_id = str(item.get('statId'))
            stat_name = stat_id_map.get(stat_id)

            if stat_name:
                if stat_name in pitching_stat_names:
                    pitching_stats.append(stat_name)
                else:
                    batting_stats.append(stat_name)

        stat_categories = {
            "batting": sorted(batting_stats),
            "pitching": sorted(pitching_stats)
        }

        return LeagueSettings(
            league_id=str(self.league_id),
            name=settings.name,
            season_year=self.season_year,
            team_count=settings.team_count,
            playoff_team_count=settings.playoff_team_count,
            reg_season_count=settings.reg_season_count,
            scoring_type=settings.scoring_type,
            # Raw settings objects from ESPN API
            acquisition_settings=raw_settings.get('acquisitionSettings', {}),
            draft_settings=raw_settings.get('draftSettings', {}),
            finance_settings=raw_settings.get('financeSettings', {}),
            roster_settings=raw_settings.get('rosterSettings', {}),
            schedule_settings=raw_settings.get('scheduleSettings', {}),
            scoring_settings=raw_settings.get('scoringSettings', {}),
            trade_settings=raw_settings.get('tradeSettings', {}),
            # Simple settings fields
            experience_type=raw_settings.get('experienceType'),
            is_public=raw_settings.get('isPublic', True),
            restriction_type=raw_settings.get('restrictionType'),
            # Computed fields
            stat_categories=stat_categories,
            stat_id_map=stat_id_map,
        )

    def get_team(self, team_id: int) -> Team:
        """Get specific team information.

        Args:
            team_id: Team ID (0-based index in teams list)

        Returns:
            Team object
        """
        espn_team = self.league.teams[team_id]

        owners = getattr(espn_team, "owners", [])
        primary_owner = owners[0] if owners else "Unknown"

        return Team(
            team_id=team_id,
            team_name=espn_team.team_name,
            team_abbrev=espn_team.team_abbrev,
            owners=owners,
            primary_owner=primary_owner,
            wins=espn_team.wins,
            losses=espn_team.losses,
            ties=getattr(espn_team, "ties", 0),
            points_for=getattr(espn_team, "points_for", 0.0),
            points_against=getattr(espn_team, "points_against", 0.0),
            standing=espn_team.standing,
        )

    def get_standings(self) -> List[Team]:
        """Get current league standings.

        Returns:
            List of Team objects sorted by standing
        """
        teams = []
        for idx, espn_team in enumerate(self.league.teams):
            owners = getattr(espn_team, "owners", [])
            primary_owner = owners[0] if owners else "Unknown"

            teams.append(
                Team(
                    team_id=idx,
                    team_name=espn_team.team_name,
                    team_abbrev=espn_team.team_abbrev,
                    owners=owners,
                    primary_owner=primary_owner,
                    wins=espn_team.wins,
                    losses=espn_team.losses,
                    ties=getattr(espn_team, "ties", 0),
                    points_for=getattr(espn_team, "points_for", 0.0),
                    points_against=getattr(espn_team, "points_against", 0.0),
                    standing=espn_team.standing,
                )
            )

        # Sort by standing
        teams.sort(key=lambda t: t.standing)
        return teams

    def get_roster(self, team_id: int) -> List[Player]:
        """Get roster for a team.

        Args:
            team_id: Team ID (0-based index in teams list)

        Returns:
            List of Player objects
        """
        espn_team = self.league.teams[team_id]
        players = []

        for espn_player in espn_team.roster:
            players.append(
                Player(
                    player_id=espn_player.playerId,
                    name=espn_player.name,
                    team=getattr(espn_player, "proTeam", ""),
                    position=getattr(espn_player, "position", ""),
                    eligible_slots=getattr(espn_player, "eligibleSlots", []),
                    lineup_slot=getattr(espn_player, "lineupSlot", None),
                    injury_status=getattr(espn_player, "injuryStatus", "ACTIVE"),
                    stats=getattr(espn_player, "stats", {}),
                    roster_status=RosterStatus.ROSTERED,
                    fantasy_team_id=team_id,
                    fantasy_team_name=espn_team.team_name,
                    fantasy_team_abbrev=espn_team.team_abbrev,
                )
            )

        return players

    def get_free_agents(
        self, size: int = 50, position: Optional[str] = None
    ) -> List[Player]:
        """Get available free agents.

        Args:
            size: Number of players to return
            position: Filter by position (e.g., 'C', '1B', 'OF', 'SP', 'RP')

        Returns:
            List of Player objects
        """
        espn_players = self.league.free_agents(size=size, position=position)
        players = []

        for espn_player in espn_players:
            # Determine if on waivers or free agent
            acquisition_type = getattr(espn_player, "acquisitionType", "")
            roster_status = RosterStatus.WAIVERS if acquisition_type == "WAIVERS" else RosterStatus.FREE_AGENT

            players.append(
                Player(
                    player_id=espn_player.playerId,
                    name=espn_player.name,
                    team=getattr(espn_player, "proTeam", ""),
                    position=getattr(espn_player, "position", ""),
                    eligible_slots=getattr(espn_player, "eligibleSlots", []),
                    lineup_slot=None,
                    injury_status=getattr(espn_player, "injuryStatus", "ACTIVE"),
                    stats=getattr(espn_player, "stats", {}),
                    roster_status=roster_status,
                    fantasy_team_id=None,
                    fantasy_team_name=None,
                    fantasy_team_abbrev=None,
                )
            )

        return players

    def _get_player_map(self) -> Dict:
        """Get cached player map or fetch if not cached.

        Returns:
            Dictionary mapping player names to IDs and vice versa
        """
        cache_key = (self.league_id, self.season_year)

        if cache_key not in _player_map_cache:
            # Cache the player_map from the league
            _player_map_cache[cache_key] = self.league.player_map

        return _player_map_cache[cache_key]

    def get_player_by_name(
        self, name: str, fuzzy_match: bool = True, fuzzy_threshold: int = 80
    ) -> Tuple[Optional[Player], List[str]]:
        """Look up a player by name.

        Args:
            name: Player name to search for
            fuzzy_match: Whether to use fuzzy matching if exact match fails
            fuzzy_threshold: Minimum score (0-100) for fuzzy matches

        Returns:
            Tuple of (Player object or None, list of suggestions if not found)
        """
        player_map = self._get_player_map()

        # Try exact match first
        if name in player_map:
            player_id = player_map[name]
            return self._find_player_by_id(player_id), []

        # If fuzzy matching is enabled, find close matches
        suggestions = []
        if fuzzy_match:
            # Get all player names (filter out numeric keys which are IDs)
            player_names = [k for k in player_map.keys() if isinstance(k, str)]

            # Use rapidfuzz to find close matches
            matches = process.extract(
                name,
                player_names,
                scorer=fuzz.WRatio,
                limit=5,
                score_cutoff=fuzzy_threshold
            )

            suggestions = [match[0] for match in matches]

        return None, suggestions

    def _find_player_by_id(self, player_id: int) -> Optional[Player]:
        """Find a player by their ID in rosters or free agents.

        Args:
            player_id: ESPN player ID

        Returns:
            Player object or None if not found
        """
        # Search in team rosters first (faster, smaller dataset)
        for team_idx, espn_team in enumerate(self.league.teams):
            for espn_player in espn_team.roster:
                if espn_player.playerId == player_id:
                    return Player(
                        player_id=espn_player.playerId,
                        name=espn_player.name,
                        team=getattr(espn_player, "proTeam", ""),
                        position=getattr(espn_player, "position", ""),
                        eligible_slots=getattr(espn_player, "eligibleSlots", []),
                        lineup_slot=getattr(espn_player, "lineupSlot", None),
                        injury_status=getattr(espn_player, "injuryStatus", "ACTIVE"),
                        stats=getattr(espn_player, "stats", {}),
                        roster_status=RosterStatus.ROSTERED,
                        fantasy_team_id=team_idx,
                        fantasy_team_name=espn_team.team_name,
                        fantasy_team_abbrev=espn_team.team_abbrev,
                    )

        # If not found in rosters, search free agents
        # Use a large size to ensure we find the player
        espn_players = self.league.free_agents(size=1000)
        for espn_player in espn_players:
            if espn_player.playerId == player_id:
                # Determine if on waivers or free agent
                acquisition_type = getattr(espn_player, "acquisitionType", "")
                roster_status = RosterStatus.WAIVERS if acquisition_type == "WAIVERS" else RosterStatus.FREE_AGENT

                return Player(
                    player_id=espn_player.playerId,
                    name=espn_player.name,
                    team=getattr(espn_player, "proTeam", ""),
                    position=getattr(espn_player, "position", ""),
                    eligible_slots=getattr(espn_player, "eligibleSlots", []),
                    lineup_slot=None,
                    injury_status=getattr(espn_player, "injuryStatus", "ACTIVE"),
                    stats=getattr(espn_player, "stats", {}),
                    roster_status=roster_status,
                    fantasy_team_id=None,
                    fantasy_team_name=None,
                    fantasy_team_abbrev=None,
                )

        return None
