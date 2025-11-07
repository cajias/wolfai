"""Complete Werewolf game engine with roles, phases, and game logic."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

# Game configuration constants
MIN_PLAYERS = 2


class Role(Enum):
    """Player roles in the Werewolf game."""

    VILLAGER = "villager"
    WEREWOLF = "werewolf"
    SEER = "seer"
    DOCTOR = "doctor"


class Phase(Enum):
    """Game phases in the Werewolf game."""

    INITIALIZED = "initialized"
    UPDATED = "updated"  # Backward compatibility phase
    NIGHT = "night"
    DAY = "day"
    VOTING = "voting"
    RESOLUTION = "resolution"
    GAME_OVER = "game_over"


@dataclass
class Player:
    """Represents a player in the game."""

    player_id: str
    role: Role
    alive: bool = True


@dataclass
class Arena:
    """Complete Werewolf game state manager.

    This class handles all game logic including:
    - Player management with hidden roles
    - Phase transitions (Night -> Day -> Voting -> Resolution)
    - Night actions (werewolf kill, seer investigate, doctor protect)
    - Voting and elimination
    - Win condition detection
    """

    # Core game state
    players: Dict[str, Player] = field(default_factory=dict)
    phase: Phase = Phase.INITIALIZED
    day_number: int = 0

    # Night actions (reset each night)
    werewolf_targets: Set[str] = field(default_factory=set)  # Werewolves vote on target
    seer_target: Optional[str] = None
    doctor_target: Optional[str] = None

    # Voting (reset each voting phase)
    votes: Dict[str, str] = field(default_factory=dict)  # voter_id -> target_id

    # Game history and public events
    actions: List[str] = field(default_factory=list)
    eliminated_players: List[str] = field(default_factory=list)

    # Private investigation results (seer only)
    investigation_results: Dict[str, List[tuple[str, str]]] = field(
        default_factory=dict
    )  # seer_id -> [(target, result), ...]

    # Game outcome
    winner: Optional[str] = None  # "werewolves", "villagers", or None

    # Track which players have acted this phase
    players_acted: Set[str] = field(default_factory=set)

    @property
    def roles(self) -> Dict[str, str]:
        """Backward compatibility property to access roles."""
        return {pid: p.role.value for pid, p in self.players.items()}

    def add_player(self, actor_id: str, role: str) -> None:
        """Register a player with a hidden role."""
        try:
            role_enum = Role(role.lower())
        except ValueError as exc:
            raise ValueError(f"Invalid role: {role}") from exc

        self.players[actor_id] = Player(player_id=actor_id, role=role_enum)

    def start_game(self) -> None:
        """Start the game and transition to first night phase."""
        if self.phase not in (Phase.INITIALIZED, Phase.UPDATED):
            raise ValueError("Game has already started")

        if len(self.players) < MIN_PLAYERS:
            raise ValueError(f"Need at least {MIN_PLAYERS} players to start")

        # Verify we have at least one werewolf
        werewolf_count = sum(1 for p in self.players.values() if p.role == Role.WEREWOLF)
        if werewolf_count == 0:
            raise ValueError("Game must have at least one werewolf")

        self.phase = Phase.NIGHT
        self.day_number = 1
        self.actions.append("Game started - Night 1 begins")

    def apply_action(self, actor_id: str, action: str) -> None:  # noqa: C901, PLR0912
        """Process a game action from a player.

        Actions can be:
        - Night actions: "kill:target_id", "investigate:target_id", "protect:target_id"
        - Votes: "vote:target_id"
        - Phase control: "advance_phase", "start_game"
        - Any other text: recorded as discussion/action log
        """
        if self.phase == Phase.GAME_OVER:
            raise ValueError("Game is over")

        # Handle special commands
        if action == "start_game":
            self.start_game()
            return

        if action == "advance_phase":
            self.advance_phase()
            return

        # Handle player actions based on current phase
        if self.phase == Phase.NIGHT:
            # Try to handle as night action, otherwise record as discussion
            if ":" in action and action.split(":", 1)[0] in ["kill", "investigate", "protect"]:
                self._handle_night_action(actor_id, action)
            else:
                # Just record it
                self.actions.append(action)
        elif self.phase == Phase.VOTING:
            # Try to handle as vote, otherwise record as discussion
            if action.startswith("vote:"):
                self._handle_vote(actor_id, action)
            else:
                self.actions.append(action)
        elif self.phase == Phase.DAY:
            # During day phase, just record discussion
            self.actions.append(action)
        elif self.phase == Phase.INITIALIZED:
            # Allow arbitrary actions during initialized phase for backward compatibility
            self.actions.append(action)
            # Change phase to UPDATED for backward compatibility
            self.phase = Phase.UPDATED
        elif self.phase == Phase.RESOLUTION:
            # During resolution, just record
            self.actions.append(action)
        else:
            # Default: just record the action
            self.actions.append(action)

    def _handle_night_action(self, actor_id: str, action: str) -> None:  # noqa: C901
        """Handle night phase actions."""
        if actor_id not in self.players:
            raise ValueError(f"Unknown player: {actor_id}")

        player = self.players[actor_id]
        if not player.alive:
            raise ValueError("Dead players cannot act")

        # Parse action
        if ":" not in action:
            raise ValueError(f"Invalid night action format: {action}")

        action_type, target_id = action.split(":", 1)

        if target_id not in self.players:
            raise ValueError(f"Unknown target: {target_id}")

        if not self.players[target_id].alive:
            raise ValueError(f"Cannot target dead player: {target_id}")

        # Process based on role
        if action_type == "kill" and player.role == Role.WEREWOLF:
            self.werewolf_targets.add(target_id)
            self.players_acted.add(actor_id)
            # Don't reveal in actions list
        elif action_type == "investigate" and player.role == Role.SEER:
            if self.seer_target is not None:
                raise ValueError("Seer has already investigated this night")
            self.seer_target = target_id
            # Store investigation result for seer
            target_role = self.players[target_id].role
            result = "werewolf" if target_role == Role.WEREWOLF else "not werewolf"
            if actor_id not in self.investigation_results:
                self.investigation_results[actor_id] = []
            self.investigation_results[actor_id].append((target_id, result))
            self.players_acted.add(actor_id)
        elif action_type == "protect" and player.role == Role.DOCTOR:
            if self.doctor_target is not None:
                raise ValueError("Doctor has already protected this night")
            self.doctor_target = target_id
            self.players_acted.add(actor_id)
        else:
            raise ValueError(
                f"Player {actor_id} with role {player.role.value} cannot perform {action_type}"
            )

    def _handle_vote(self, voter_id: str, action: str) -> None:
        """Handle voting phase actions."""
        if voter_id not in self.players:
            raise ValueError(f"Unknown player: {voter_id}")

        player = self.players[voter_id]
        if not player.alive:
            raise ValueError("Dead players cannot vote")

        if not action.startswith("vote:"):
            raise ValueError(f"Invalid vote format: {action}")

        target_id = action.split(":", 1)[1]

        if target_id not in self.players:
            raise ValueError(f"Unknown target: {target_id}")

        if not self.players[target_id].alive:
            raise ValueError(f"Cannot vote for dead player: {target_id}")

        self.votes[voter_id] = target_id
        self.players_acted.add(voter_id)

    def advance_phase(self) -> None:
        """Advance to the next game phase."""
        if self.phase in (Phase.INITIALIZED, Phase.UPDATED):
            self.start_game()
        elif self.phase == Phase.NIGHT:
            self._resolve_night()
        elif self.phase == Phase.DAY:
            self._start_voting()
        elif self.phase == Phase.VOTING:
            self._resolve_voting()
        elif self.phase == Phase.RESOLUTION:
            self._start_next_day()
        elif self.phase == Phase.GAME_OVER:
            raise ValueError("Game is already over")

    def _resolve_night(self) -> None:
        """Resolve night actions and transition to day."""
        # Determine if anyone dies
        killed_player: Optional[str] = None

        # Werewolves choose victim (majority vote among werewolves)
        if self.werewolf_targets:
            # For simplicity, if multiple targets, pick the first one
            # In a real game, this would be a vote
            killed_player = list(self.werewolf_targets)[0]

        # Doctor can save the victim
        if killed_player and killed_player == self.doctor_target:
            self.actions.append(f"Night {self.day_number}: No one died (doctor saved)")
            killed_player = None
        elif killed_player:
            self.players[killed_player].alive = False
            self.eliminated_players.append(killed_player)
            self.actions.append(
                f"Night {self.day_number}: A player was killed by werewolves"
            )
        else:
            self.actions.append(f"Night {self.day_number}: No one died")

        # Reset night actions
        self.werewolf_targets.clear()
        self.seer_target = None
        self.doctor_target = None
        self.players_acted.clear()

        # Check win condition
        if self._check_win_condition():
            self.phase = Phase.GAME_OVER
            return

        # Transition to day
        self.phase = Phase.DAY
        self.actions.append(f"Day {self.day_number} begins - Discussion phase")

    def _start_voting(self) -> None:
        """Transition from day to voting phase."""
        self.phase = Phase.VOTING
        self.votes.clear()
        self.players_acted.clear()
        self.actions.append(f"Day {self.day_number}: Voting phase begins")

    def _resolve_voting(self) -> None:
        """Resolve votes and eliminate a player."""
        if not self.votes:
            self.actions.append(f"Day {self.day_number}: No votes cast, no elimination")
        else:
            # Count votes
            vote_counts: Dict[str, int] = {}
            for target_id in self.votes.values():
                vote_counts[target_id] = vote_counts.get(target_id, 0) + 1

            # Find player with most votes
            max_votes = max(vote_counts.values())
            candidates = [pid for pid, count in vote_counts.items() if count == max_votes]

            if len(candidates) > 1:
                # Tie - no elimination
                self.actions.append(
                    f"Day {self.day_number}: Vote tied, no elimination"
                )
            else:
                eliminated = candidates[0]
                self.players[eliminated].alive = False
                self.eliminated_players.append(eliminated)
                eliminated_role = self.players[eliminated].role.value
                self.actions.append(
                    f"Day {self.day_number}: Player eliminated by vote "
                    f"(was {eliminated_role})"
                )

        self.votes.clear()
        self.players_acted.clear()
        self.phase = Phase.RESOLUTION

        # Check win condition
        self._check_win_condition()

    def _start_next_day(self) -> None:
        """Start the next night phase."""
        if self.phase == Phase.GAME_OVER:
            return

        self.day_number += 1
        self.phase = Phase.NIGHT
        self.actions.append(f"Night {self.day_number} begins")

    def _check_win_condition(self) -> bool:
        """Check if the game has ended and set winner."""
        alive_players = [p for p in self.players.values() if p.alive]
        alive_werewolves = [p for p in alive_players if p.role == Role.WEREWOLF]
        alive_villagers = [
            p for p in alive_players if p.role != Role.WEREWOLF
        ]

        if len(alive_werewolves) == 0:
            self.winner = "villagers"
            self.phase = Phase.GAME_OVER
            self.actions.append("Game Over: Villagers win! All werewolves eliminated")
            return True
        elif len(alive_werewolves) >= len(alive_villagers):
            self.winner = "werewolves"
            self.phase = Phase.GAME_OVER
            self.actions.append(
                "Game Over: Werewolves win! They equal or outnumber the villagers"
            )
            return True

        return False

    def public_view(self) -> Dict[str, Any]:
        """Return data safe for public consumption.

        This hides player roles and returns only publicly visible information.
        """
        alive_players = [pid for pid, p in self.players.items() if p.alive]
        dead_players = [pid for pid, p in self.players.items() if not p.alive]

        return {
            "state": self.phase.value,
            "actions": self.actions,
            "day_number": self.day_number,
            "alive_players": alive_players,
            "dead_players": dead_players,
            "winner": self.winner,
            "player_count": len(self.players),
        }

    def get_player_view(self, player_id: str) -> Dict[str, Any]:
        """Return what a specific player can see.

        Includes their role, investigation results (if seer), etc.
        """
        if player_id not in self.players:
            raise ValueError(f"Unknown player: {player_id}")

        player = self.players[player_id]
        view = self.public_view()

        # Add private information for this player
        view["your_role"] = player.role.value
        view["your_status"] = "alive" if player.alive else "dead"

        # Add investigation results if seer
        if player.role == Role.SEER and player_id in self.investigation_results:
            view["investigations"] = self.investigation_results[player_id]

        # Show other werewolves if this player is a werewolf
        if player.role == Role.WEREWOLF:
            view["fellow_werewolves"] = [
                pid
                for pid, p in self.players.items()
                if p.role == Role.WEREWOLF and pid != player_id
            ]

        return view

    def get_valid_actions(self, player_id: str) -> List[str]:  # noqa: C901
        """Return list of valid actions for a player in the current phase."""
        if player_id not in self.players:
            return []

        player = self.players[player_id]
        if not player.alive:
            return []

        valid_actions = []

        if self.phase in (Phase.INITIALIZED, Phase.UPDATED):
            return ["start_game", "advance_phase"]

        if self.phase == Phase.NIGHT:
            alive_others = [
                pid for pid, p in self.players.items()
                if p.alive and pid != player_id
            ]

            if player.role == Role.WEREWOLF and player_id not in self.players_acted:
                valid_actions.extend([f"kill:{pid}" for pid in alive_others])
            elif player.role == Role.SEER and player_id not in self.players_acted:
                valid_actions.extend([f"investigate:{pid}" for pid in alive_others])
            elif player.role == Role.DOCTOR and player_id not in self.players_acted:
                valid_actions.extend([f"protect:{pid}" for pid in alive_others])

            valid_actions.append("advance_phase")

        elif self.phase == Phase.DAY:
            valid_actions.append("advance_phase")

        elif self.phase == Phase.VOTING:
            if player_id not in self.players_acted:
                alive_others = [
                    pid for pid, p in self.players.items()
                    if p.alive and pid != player_id
                ]
                valid_actions.extend([f"vote:{pid}" for pid in alive_others])
            valid_actions.append("advance_phase")

        elif self.phase == Phase.RESOLUTION:
            valid_actions.append("advance_phase")

        return valid_actions
