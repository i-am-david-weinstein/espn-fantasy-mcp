# Tool Reference

All tools use `league_id`, `season_year`, and (where applicable) `team_id` from your environment configuration by default. You only need to pass these explicitly to override them.

Transaction tools (`add_free_agent`, `drop_player`, `claim_waiver`, `propose_trade`, `cancel_trade`, `accept_trade`, `decline_trade`) use a **confirmation pattern**: the first call (default `confirm=false`) returns a preview; pass `confirm=true` to execute.

---

## League

### `get_league_settings`
Get league configuration including scoring categories and roster settings.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `league_id` | No | ESPN League ID (defaults to configured league) |
| `season_year` | No | Season year (defaults to configured year) |

### `get_standings`
Get current league standings with team records and rankings.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `league_id` | No | ESPN League ID (defaults to configured league) |
| `season_year` | No | Season year |

---

## Teams

### `get_team`
Get information about a specific team.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `team_id` | **Yes** | Team ID (0-based index) |
| `league_id` | No | ESPN League ID |
| `season_year` | No | Season year |

### `get_roster`
Get the current roster for a team with player details and lineup positions.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `team_id` | **Yes** | Team ID (0-based index) |
| `league_id` | No | ESPN League ID |
| `season_year` | No | Season year |

---

## Players

### `get_free_agents`
Get available free agents, optionally filtered by position.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `position` | No | Filter by position: `C`, `1B`, `2B`, `SS`, `3B`, `OF`, `SP`, `RP`, `P` |
| `size` | No | Number of results to return (default: 50) |
| `league_id` | No | ESPN League ID |
| `season_year` | No | Season year |

### `get_player_info`
Look up a player by name. Supports fuzzy matching — if an exact match isn't found, similar names are suggested.

Returns MLB team, position, fantasy eligibility, roster status, and actual/projected stats.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `player_name` | **Yes** | Player's full name (e.g., `Shohei Ohtani`) |
| `league_id` | No | ESPN League ID |
| `season_year` | No | Season year |

---

## Roster

### `modify_lineup`
Move players between lineup slots. Validates all moves before executing; returns errors without making changes if any move is invalid.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `team_id` | **Yes** | Team ID (0-based index) |
| `moves` | **Yes** | List of moves, each with `player_id`, `from_slot`, `to_slot` |
| `confirm` | No | `false` (default) previews; `true` executes |
| `scoring_period_id` | No | Scoring period (defaults to current) |
| `league_id` | No | ESPN League ID |
| `season_year` | No | Season year |

---

## Transactions

### `get_pending_transactions`
Get waiver claims and trade proposals, including PENDING, EXECUTED, and CANCELED statuses. For trades, returns both sent and received proposals.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `team_id` | No | Team ID. If omitted, returns all transactions league-wide. |
| `league_id` | No | ESPN League ID |
| `season_year` | No | Season year |

### `add_free_agent`
Add a free agent directly to your team, bypassing waivers. If your roster is full, you must provide `drop_player_id`.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `team_id` | **Yes** | Team ID (0-based index) |
| `add_player_id` | **Yes** | ESPN player ID to add |
| `drop_player_id` | No | ESPN player ID to drop (required if roster is full) |
| `confirm` | No | `false` previews; `true` executes |
| `scoring_period_id` | No | Scoring period (defaults to current) |
| `league_id` | No | ESPN League ID |
| `season_year` | No | Season year |

### `drop_player`
Drop a player from your team.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `team_id` | **Yes** | Team ID (0-based index) |
| `player_id` | **Yes** | ESPN player ID to drop |
| `confirm` | No | `false` previews; `true` executes |
| `scoring_period_id` | No | Scoring period (defaults to current) |
| `league_id` | No | ESPN League ID |
| `season_year` | No | Season year |

### `claim_waiver`
Submit a waiver claim with an optional FAAB bid. Claims are queued and processed during waiver periods. If your roster is full, you must provide `drop_player_id`.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `team_id` | **Yes** | Team ID (0-based index) |
| `add_player_id` | **Yes** | ESPN player ID to claim |
| `drop_player_id` | No | ESPN player ID to drop (required if roster is full) |
| `bid_amount` | No | FAAB bid amount (default: 0) |
| `confirm` | No | `false` previews; `true` submits |
| `scoring_period_id` | No | Scoring period (defaults to current) |
| `league_id` | No | ESPN League ID |
| `season_year` | No | Season year |

### `cancel_waiver`
Cancel a pending waiver claim. Requires the transaction ID from the original claim (returned by `claim_waiver` or `get_pending_transactions`).

| Parameter | Required | Description |
|-----------|----------|-------------|
| `team_id` | **Yes** | Team ID (0-based index) |
| `transaction_id` | **Yes** | Transaction ID from the original waiver claim |
| `confirm` | No | `false` previews; `true` cancels |
| `scoring_period_id` | No | Scoring period (defaults to current) |
| `league_id` | No | ESPN League ID |
| `season_year` | No | Season year |

### `propose_trade`
Propose a trade with another team. Returns a transaction ID that can be used with `cancel_trade`.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `team_id` | **Yes** | Your team ID (0-based index) |
| `receiving_team_id` | **Yes** | The other team's ID |
| `send_player_ids` | **Yes** | List of player IDs you are sending |
| `receive_player_ids` | **Yes** | List of player IDs you want to receive |
| `comment` | No | Message to include with the offer |
| `expiration_days` | No | Days until the offer expires (default: 7) |
| `confirm` | No | `false` previews; `true` sends |
| `scoring_period_id` | No | Scoring period (defaults to current) |
| `league_id` | No | ESPN League ID |
| `season_year` | No | Season year |

### `cancel_trade`
Cancel a pending trade proposal you sent.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `team_id` | **Yes** | Your team ID (0-based index) |
| `transaction_id` | **Yes** | Transaction ID from the original proposal |
| `confirm` | No | `false` previews; `true` cancels |
| `scoring_period_id` | No | Scoring period (defaults to current) |
| `league_id` | No | ESPN League ID |
| `season_year` | No | Season year |

### `accept_trade`
Accept a pending trade offer from another team.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `team_id` | **Yes** | Your team ID (0-based index) |
| `transaction_id` | **Yes** | Transaction ID of the trade proposal |
| `confirm` | No | `false` previews; `true` accepts |
| `scoring_period_id` | No | Scoring period (defaults to current) |
| `league_id` | No | ESPN League ID |
| `season_year` | No | Season year |

### `decline_trade`
Decline a trade offer from another team.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `team_id` | **Yes** | Your team ID (0-based index) |
| `transaction_id` | **Yes** | Transaction ID of the trade proposal |
| `comment` | No | Reason for declining |
| `confirm` | No | `false` previews; `true` declines |
| `scoring_period_id` | No | Scoring period (defaults to current) |
| `league_id` | No | ESPN League ID |
| `season_year` | No | Season year |
