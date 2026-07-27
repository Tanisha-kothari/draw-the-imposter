from enum import Enum


class GamePhase(str, Enum):
    LOBBY = "lobby"
    READY = "ready"
    ASSIGN_ROLES = "assign_roles"
    DRAWING = "drawing"
    REVEAL = "reveal"
    VOTING = "voting"
    RESULTS = "results"
    GAME_OVER = "game_over"


PHASE_DURATIONS: dict[GamePhase, int] = {
    GamePhase.LOBBY: 0,
    GamePhase.READY: 0,
    GamePhase.ASSIGN_ROLES: 5,
    GamePhase.DRAWING: 60,
    GamePhase.REVEAL: 15,
    GamePhase.VOTING: 30,
    GamePhase.RESULTS: 10,
    GamePhase.GAME_OVER: 0,
}

VALID_TRANSITIONS: dict[GamePhase, set[GamePhase]] = {
    GamePhase.LOBBY: {GamePhase.READY},
    GamePhase.READY: {GamePhase.ASSIGN_ROLES},
    GamePhase.ASSIGN_ROLES: {GamePhase.DRAWING},
    GamePhase.DRAWING: {GamePhase.REVEAL},
    GamePhase.REVEAL: {GamePhase.VOTING},
    GamePhase.VOTING: {GamePhase.RESULTS},
    GamePhase.RESULTS: {GamePhase.DRAWING, GamePhase.GAME_OVER},
    GamePhase.GAME_OVER: {GamePhase.LOBBY},
}


class StateMachineError(Exception):
    """Raised when an invalid state transition is attempted."""


class StateMachine:
    """Manages game phase transitions with server-authoritative validation."""

    def __init__(self) -> None:
        self._current_phase: GamePhase = GamePhase.LOBBY

    @property
    def current_phase(self) -> GamePhase:
        return self._current_phase

    def transition(self, target_phase: GamePhase) -> GamePhase:
        """Validate and execute a phase transition.

        Args:
            target_phase: The phase to transition to.

        Returns:
            The new current phase.

        Raises:
            StateMachineError: If the transition is not allowed.
        """
        allowed = VALID_TRANSITIONS.get(self._current_phase, set())
        if target_phase not in allowed:
            raise StateMachineError(
                f"Cannot transition from '{self._current_phase.value}' "
                f"to '{target_phase.value}'. Allowed: {[p.value for p in allowed]}"
            )
        self._current_phase = target_phase
        return self._current_phase

    @staticmethod
    def get_phase_duration(phase: GamePhase, config_drawing_time: int = 60, config_voting_time: int = 30) -> int:
        """Get the duration in seconds for a given phase.

        Args:
            phase: The game phase.
            config_drawing_time: Room-configured drawing time.
            config_voting_time: Room-configured voting time.

        Returns:
            Duration in seconds.
        """
        if phase == GamePhase.DRAWING:
            return config_drawing_time
        if phase == GamePhase.VOTING:
            return config_voting_time
        return PHASE_DURATIONS.get(phase, 0)

    def reset(self) -> None:
        """Reset the state machine back to LOBBY."""
        self._current_phase = GamePhase.LOBBY
