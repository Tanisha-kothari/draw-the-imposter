import logging
import random
import uuid

from app.models.game import Game
from app.models.player import Player
from app.models.room import Room
from app.repositories.game_repository import GameRepository
from app.repositories.player_repository import PlayerRepository
from app.repositories.room_repository import RoomRepository
from app.schemas.game import GameState, PlayerState
from app.utils.game_state_machine import GamePhase, StateMachine
from app.utils.words import word_bank


class GameService:
    def __init__(self) -> None:
        self._game_repo = GameRepository()
        self._player_repo = PlayerRepository()
        self._room_repo = RoomRepository()
        # Per-game used-word history to prevent immediate repetition
        self._used_words: dict[uuid.UUID, set[str]] = {}

    async def create_game(self, room: Room) -> Game:
        game = await self._game_repo.create(
            room_id=room.id,
            current_round=0,
            current_phase=GamePhase.READY.value,
        )
        await self._room_repo.update_status(room.id, "playing")
        return game

    async def assign_roles(self, game: Game, players: list[Player], num_imposters: int) -> list[Player]:
        imposters = random.sample(players, min(num_imposters, len(players)))
        imposter_ids = {p.id for p in imposters}

        updated = []
        for player in players:
            is_imp = player.id in imposter_ids
            role = "imposter" if is_imp else "artist"
            updated_player = await self._player_repo.update_role(player.id, role, is_imp)
            if updated_player:
                updated.append(updated_player)

        return updated

    async def select_word(self, game: Game, category: str | None = None, difficulty: str = "medium") -> tuple[str, str]:
        used = self._used_words.get(game.id)
        _word, _cat, _diff = word_bank.get_random_word(category or None, difficulty, exclude=used)
        self._used_words.setdefault(game.id, set()).add(_word)
        await self._game_repo.set_word(game.id, _word, _cat)
        game.word = _word
        game.category = _cat
        return _word, _cat

    async def start_next_round(self, game: Game, imposter_ids: list[uuid.UUID] | None = None) -> Game:
        next_round = game.current_round + 1
        word = game.word or ""
        category = getattr(game, 'category', None) or ""
        primary_imposter_id = imposter_ids[0] if imposter_ids else None
        if not imposter_ids and game.current_round >= 0:
            logger = logging.getLogger(__name__)
            logger.warning("[ROUND] start_next_round round=%d: no imposter_ids provided", next_round)
        await self._game_repo.update_round(game.id, next_round, word)
        await self._game_repo.create_round(game.id, next_round, word, GamePhase.DRAWING.value, category=category, imposter_id=primary_imposter_id)
        updated = await self._game_repo.update_phase(game.id, GamePhase.DRAWING.value)
        return updated or game

    def clear_word_history(self, game_id: uuid.UUID) -> None:
        """Clear the used-word history for a game (called on game end / play again)."""
        self._used_words.pop(game_id, None)

    async def calculate_results(self, game: Game) -> dict:
        from app.repositories.vote_repository import VoteRepository
        vote_repo = VoteRepository()

        room = await self._room_repo.get_by_id(game.room_id)
        players = await self._player_repo.get_by_room(game.room_id)
        votes = await vote_repo.get_by_game(game.id)

        imposters = [p for p in players if p.is_imposter]
        artists = [p for p in players if not p.is_imposter]

        round_votes = [v for v in votes if v.round_number == game.current_round]

        imposter_votes = sum(1 for v in round_votes if v.target_id in {i.id for i in imposters})
        total_votes = len(round_votes)

        if imposters and imposter_votes >= len(imposters):
            for imp in imposters:
                await self._player_repo.update_score(imp.id, imp.score - 1)
            for artist in artists:
                await self._player_repo.update_score(artist.id, artist.score + 1)
            return {"winner": "artists", "imposters_caught": True}
        else:
            for imp in imposters:
                await self._player_repo.update_score(imp.id, imp.score + 2)
            return {"winner": "imposters", "imposters_caught": False}

    async def get_game_state(self, game_id: uuid.UUID) -> GameState:
        game = await self._game_repo.get_by_id(game_id)
        if not game:
            raise ValueError("Game not found")

        room = await self._room_repo.get_by_id(game.room_id)
        players = await self._player_repo.get_by_room(game.room_id)

        return GameState(
            phase=game.current_phase,
            round=game.current_round,
            word_hint=game.word[:3] + "..." if game.word else None,
            time_remaining=0,
            players=[
                PlayerState(
                    id=p.id,
                    nickname=p.nickname,
                    score=p.score,
                    is_ready=p.is_ready,
                    is_host=p.is_host,
                    is_imposter=p.is_imposter,
                )
                for p in players
            ],
        )

    async def validate_transition(self, game: Game, target_phase: GamePhase) -> bool:
        sm = StateMachine()
        sm._current_phase = GamePhase(game.current_phase)
        try:
            sm.transition(target_phase)
            return True
        except Exception:
            return False

    async def handle_disconnect(self, game: Game, player_id: uuid.UUID) -> dict:
        player = await self._player_repo.get_by_id(player_id)
        if not player:
            return {"action": "none", "reason": "player_not_found"}

        await self._player_repo.set_connected(player_id, False)

        room = await self._room_repo.get_by_id(game.room_id)
        if not room:
            return {"action": "none", "reason": "room_not_found"}

        # Fetch players via repository — avoids lazy-loading room.players on a detached Room
        all_players = await self._player_repo.get_by_room(room.id)
        connected = [p for p in all_players if p.is_connected and p.id != player_id]

        if player.is_host and connected:
            new_host = connected[0]
            await self._player_repo.transfer_host(room.id, new_host.id)

        if game.current_phase == GamePhase.LOBBY.value:
            return {"action": "removed_from_lobby", "reason": "player_disconnected"}

        remaining = len(connected)
        if remaining < 2:
            return {"action": "end_game", "reason": "not_enough_players"}

        return {"action": "pause", "reason": "player_disconnected"}
