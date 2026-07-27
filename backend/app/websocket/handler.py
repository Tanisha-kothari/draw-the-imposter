import asyncio
import logging
import random
from typing import Any

import uuid

from app.repositories.game_repository import GameRepository
from app.repositories.player_repository import PlayerRepository
from app.repositories.room_repository import RoomRepository
from app.services.drawing_service import DrawingService
from app.services.game_service import GameService
from app.services.room_service import RoomService
from app.services.vote_service import VoteService
from app.utils.game_state_machine import GamePhase, StateMachine
from app.utils.room_serializer import serialize_room
from app.websocket.manager import ConnectionManager

logger = logging.getLogger(__name__)


class MessageHandler:
    """Server-authoritative WebSocket message handler with turn management."""

    def __init__(self, manager: ConnectionManager) -> None:
        self.manager = manager
        self._room_repo = RoomRepository()
        self._player_repo = PlayerRepository()
        self._game_repo = GameRepository()
        self._room_service = RoomService()
        self._game_service = GameService()
        self._drawing_service = DrawingService()
        self._vote_service = VoteService()
        self._timers: dict[str, asyncio.Task] = {}
        self._turn_order: dict[str, list[str]] = {}
        self._current_turn_idx: dict[str, int] = {}
        self._disconnect_timers: dict[str, asyncio.Task] = {}
        self._player_join_order: dict[str, list[str]] = {}
        # Guard against double-resolving the same room+round
        self._voting_resolved: dict[str, int] = {}

    async def _broadcast_game_state(
        self,
        room_code: str,
        game,
        active_player_id: str | None = None,
        timer_remaining: int = 0,
        timer_phase: str = "",
        turn_number: int | None = None,
        total_turns: int | None = None,
    ) -> None:
        """Broadcast the authoritative game state to all connected clients.
        
        This is the single source of truth for:
          - current game phase
          - active player
          - turn info
          - timer
          - round
          - player list
        """
        room = await self._room_repo.get_by_code(room_code)
        if not room:
            return
        players = await self._player_repo.get_by_room(room.id)
        state = {
            "phase": game.current_phase,
            "current_round": game.current_round,
            "total_rounds": room.num_rounds,
            "current_turn_player_id": active_player_id,
            "timer_remaining": timer_remaining,
            "timer_phase": timer_phase,
            "players": [
                {
                    "id": str(p.id),
                    "nickname": p.nickname,
                    "score": p.score,
                    "is_host": p.is_host,
                    "is_connected": p.is_connected,
                }
                for p in players
            ],
        }
        if turn_number is not None:
            state["turn_number"] = turn_number
        if total_turns is not None:
            state["total_turns"] = total_turns

        logger.info("[GAME_STATE] phase=%s active=%s timer=%d turn=%s/%s in %s",
                    game.current_phase, active_player_id, timer_remaining,
                    turn_number, total_turns, room_code)

        await self.manager.broadcast_to_room(room_code, {
            "type": "game_state_updated",
            "data": state,
        })

    async def _broadcast_room(self, room_code: str) -> None:
        """Fetch the latest room state and broadcast room_updated to all connected clients."""
        room = await self._room_repo.get_by_code(room_code)
        if not room:
            return
        players = await self._player_repo.get_by_room(room.id)
        room_data = serialize_room(room, players)
        logger.info("[BROADCAST] Room %s - state: %d players, host=%s",
                    room_code, len(players), room_data.get("host_id"))
        await self.manager.broadcast_to_room(room_code, {
            "type": "room_updated",
            "data": room_data,
        })

    async def handle_message(self, room_code: str, player_id: str, message: dict[str, Any]) -> None:
        msg_type = message.get("type", "")
        data = message.get("data", {})

        logger.debug("[MSG] %s from %s in %s", msg_type, player_id, room_code)

        handlers = {
            "join_room": self.handle_join,
            "leave_room": self.handle_leave,
            "ready": self.handle_ready,
            "start_game": self.handle_start_game,
            "drawing_submit": self.handle_drawing_submit,
            "vote_submit": self.handle_vote_submit,
            "chat_message": self.handle_chat,
            "disconnect": self.handle_disconnect,
            "play_again": self.handle_play_again,
            "kick_player": self.handle_kick_player,
            "update_settings": self.handle_update_settings,
            "next_round": self.handle_next_round,
        }

        handler = handlers.get(msg_type)
        if handler:
            try:
                await handler(room_code, player_id, data)
            except Exception as e:
                logger.error("[ERROR] handling %s from %s in %s: %s", msg_type, player_id, room_code, e)
                await self.manager.send_to_player(
                    room_code, player_id,
                    {"type": "error", "data": {"message": str(e)}},
                )
        else:
            await self.manager.send_to_player(
                room_code, player_id,
                {"type": "error", "data": {"message": f"Unknown message type: {msg_type}"}},
            )

    async def handle_join(self, room_code: str, player_id: str, data: dict[str, Any]) -> None:
        player = await self._player_repo.get_by_id(uuid.UUID(player_id))
        if not player:
            raise ValueError("Player not found")

        # Cancel any pending disconnect timeout
        timer = self._disconnect_timers.pop(player_id, None)
        if timer:
            timer.cancel()
            logger.info("[RECONNECT] Player %s reconnected — disconnect timer cancelled", player_id)

        was_disconnected = not player.is_connected
        await self._player_repo.set_connected(uuid.UUID(player_id), True)
        logger.info("[JOIN_WS] Player %s connected (was_disconnected=%s) in %s", player_id, was_disconnected, room_code)

        # Track join order for host transfer (oldest first)
        if room_code not in self._player_join_order:
            self._player_join_order[room_code] = []
        if player_id not in self._player_join_order[room_code]:
            self._player_join_order[room_code].append(player_id)

        await self._broadcast_room(room_code)

    async def handle_leave(self, room_code: str, player_id: str, data: dict[str, Any] | None = None) -> None:
        player = await self._player_repo.get_by_id(uuid.UUID(player_id))
        if not player:
            return

        was_host = player.is_host
        await self._player_repo.kick(uuid.UUID(player_id))
        self.manager.disconnect(room_code, player_id)

        logger.info("[LEAVE] Player %s left room %s (was_host=%s)", player_id, room_code, was_host)

        room = await self._room_repo.get_by_code(room_code)
        if room:
            remaining = await self._player_repo.get_by_room(room.id)
            if was_host and remaining:
                # Transfer to player who has been in the room longest (by created_at / join order)
                new_host = remaining[0]  # sorted by created_at ASC
                await self._player_repo.transfer_host(room.id, new_host.id)
                logger.info("[HOST_TRANSFER] Host transferred to %s (%s) — longest-connected", new_host.nickname, new_host.id)
                await self.manager.broadcast_to_room(
                    room_code,
                    {"type": "host_changed", "data": {"host_id": str(new_host.id)}},
                )

            if not remaining:
                logger.info("[ROOM] Room %s is empty, deleting", room_code)
                await self._room_repo.delete(room.id)
                await self.manager.disconnect_all(room_code)
                self._player_join_order.pop(room_code, None)
                return

        await self._broadcast_room(room_code)

    async def handle_ready(self, room_code: str, player_id: str, data: dict[str, Any]) -> None:
        is_ready = data.get("is_ready", True)
        player = await self._player_repo.update_ready(uuid.UUID(player_id), is_ready)
        if not player:
            raise ValueError("Player not found")

        logger.info("[READY] Player %s ready=%s in %s", player_id, is_ready, room_code)
        await self._broadcast_room(room_code)

    async def handle_start_game(self, room_code: str, host_player_id: str, data: dict[str, Any]) -> None:
        player = await self._player_repo.get_by_id(uuid.UUID(host_player_id))
        if not player or not player.is_host:
            raise ValueError("Only the host can start the game")

        room = await self._room_repo.get_by_code(room_code)
        if not room:
            raise ValueError("Room not found")

        players = await self._player_repo.get_by_room(room.id)
        connected = [p for p in players if p.is_connected]
        if len(connected) < 2:
            raise ValueError("Need at least 2 players to start")

        game = await self._game_service.create_game(room)
        updated_players = await self._game_service.assign_roles(game, connected, room.num_imposters)
        word, category = await self._game_service.select_word(game, room.word_category, room.difficulty)
        imposter_ids = [p.id for p in updated_players if p.is_imposter]
        game = await self._game_service.start_next_round(game, imposter_ids)

        await self.manager.broadcast_to_room(
            room_code,
            {"type": "phase_change", "data": {"phase": "assign_roles"}},
        )
        await asyncio.sleep(2)

        players_updated = await self._player_repo.get_by_room(room.id)
        turn_order = [str(p.id) for p in players_updated if p.is_connected]
        random.shuffle(turn_order)
        self._turn_order[room_code] = turn_order
        self._current_turn_idx[room_code] = 0

        for p in players_updated:
            if p.is_imposter:
                await self.manager.send_to_player(
                    room_code, str(p.id),
                    {
                        "type": "word_assigned",
                        "data": {
                            "word_hint": None,
                            "category": category,
                            "is_imposter": True,
                            "role": "imposter",
                            "message": "You are the Imposter. You do not know today's word. Try to blend in.",
                        },
                    },
                )
            else:
                await self.manager.send_to_player(
                    room_code, str(p.id),
                    {
                        "type": "word_assigned",
                        "data": {
                            "word_hint": word,
                            "category": category,
                            "is_imposter": False,
                            "role": "artist",
                        },
                    },
                )

        await self._advance_turn(room_code, game)

    async def _advance_turn(self, room_code: str, game) -> None:
        turn_order = self._turn_order.get(room_code, [])
        current_idx = self._current_turn_idx.get(room_code, 0)

        if current_idx >= len(turn_order):
            await self._end_drawing_phase(room_code, game)
            return

        current_player_id = turn_order[current_idx]
        room = await self._room_repo.get_by_code(room_code)

        # Fetch all completed strokes (from prior turns) for shared canvas
        drawings = await self._drawing_service.get_round_drawings(game.id, game.current_round)
        existing_strokes = []
        for d in drawings:
            if d.get("stroke_data"):
                existing_strokes.extend(d["stroke_data"])

        logger.info("[TURN_START] Turn %d/%d — active_player=%s, existing_strokes=%d in %s",
                    current_idx + 1, len(turn_order), current_player_id, len(existing_strokes), room_code)

        # Broadcast the updated shared canvas
        await self.manager.broadcast_to_room(
            room_code,
            {"type": "canvas_updated", "data": {"strokes": existing_strokes}},
        )

        # Start turn timer
        timer_task = self.start_timer(room_code, "drawing", room.drawing_time)
        self._timers[room_code + "_phase"] = timer_task

        # Broadcast authoritative game state (replaces separate phase_change + turn_change)
        await self._broadcast_game_state(
            room_code, game,
            active_player_id=current_player_id,
            timer_remaining=room.drawing_time,
            timer_phase="drawing",
            turn_number=current_idx + 1,
            total_turns=len(turn_order),
        )

    async def _end_drawing_phase(self, room_code: str, game) -> None:
        await self.stop_timer(room_code + "_phase")
        fresh_game = await self._game_repo.update_phase(game.id, GamePhase.REVEAL.value) or game

        drawings = await self._drawing_service.get_round_drawings(fresh_game.id, fresh_game.current_round)
        # Flatten all strokes in submission order (temporal order)
        combined_strokes = []
        for d in drawings:
            if d.get("stroke_data"):
                combined_strokes.extend(d["stroke_data"])

        logger.info("[ROUND_COMPLETE] All %d turns finished — combined %d strokes from %d submissions in %s",
                    len(drawings), len(combined_strokes), len(drawings), room_code)

        shuffled = list(drawings)
        random.shuffle(shuffled)
        for i, d in enumerate(shuffled):
            d["player_number"] = i + 1

        await self._broadcast_game_state(
            room_code, fresh_game,
            timer_remaining=0,
            timer_phase="reveal",
        )
        await self.manager.broadcast_to_room(
            room_code,
            {
                "type": "phase_change",
                "data": {"phase": "reveal"},
            },
        )
        await self.manager.broadcast_to_room(
            room_code,
            {
                "type": "reveal_drawings",
                "data": {
                    "drawings": shuffled,
                    "combined_strokes": combined_strokes,
                },
            },
        )

        await asyncio.sleep(3)
        await self._start_voting_phase(room_code, fresh_game)

    async def _start_voting_phase(self, room_code: str, game) -> None:
        fresh_game = await self._game_repo.update_phase(game.id, GamePhase.VOTING.value) or game

        # Clear any stale guard from a previous round
        self._voting_resolved.pop(room_code, None)

        room = await self._room_repo.get_by_code(room_code)

        # Start voting countdown timer (store in _timers so it can be cancelled)
        timer_task = self.start_timer(room_code, "voting", room.voting_time)
        self._timers[room_code + "_vote_countdown"] = timer_task
        # Start auto-resolve task (runs after timeout)
        self._timers[room_code + "_vote_timeout"] = asyncio.create_task(
            self._auto_resolve_voting(room_code, fresh_game, room.voting_time)
        )

        # Broadcast authoritative game state
        await self._broadcast_game_state(
            room_code, fresh_game,
            timer_remaining=room.voting_time,
            timer_phase="voting",
        )
        # Legacy phase_change for compatibility
        await self.manager.broadcast_to_room(
            room_code,
            {"type": "phase_change", "data": {"phase": "voting"}},
        )

    async def _auto_resolve_voting(self, room_code: str, game, timeout: int) -> None:
        try:
            await asyncio.sleep(timeout)
            logger.info("[VOTE_TIMER] Timeout reached (%ds) — auto-resolving voting in %s", timeout, room_code)
            await self._resolve_round(room_code, game)
        except asyncio.CancelledError:
            logger.info("[VOTE_TIMER] Cancelled (all votes received early) in %s", room_code)
        except Exception as e:
            logger.error("[VOTE_TIMER] Error during auto-resolve in %s: %s", room_code, e, exc_info=True)

    async def handle_drawing_submit(self, room_code: str, player_id: str, data: dict[str, Any]) -> None:
        player = await self._player_repo.get_by_id(uuid.UUID(player_id))
        if not player:
            raise ValueError("Player not found")

        game = await self._game_repo.get_by_room(player.room_id)
        if not game or game.current_phase != GamePhase.DRAWING.value:
            raise ValueError("Not in drawing phase")

        turn_order = self._turn_order.get(room_code, [])
        current_idx = self._current_turn_idx.get(room_code, 0)
        if current_idx < len(turn_order) and turn_order[current_idx] != player_id:
            raise ValueError("It is not your turn")

        stroke_data = data.get("stroke_data")
        logger.info("[DRAWING_SUBMIT] Player %s submitted %d strokes (turn %d/%d) in %s",
                    player_id, len(stroke_data) if stroke_data else 0,
                    current_idx + 1, len(turn_order), room_code)

        valid, error = self._drawing_service.validate_drawing(data)
        if not valid:
            raise ValueError(error)

        await self._drawing_service.save_drawing(
            game, player, game.current_round,
            data.get("image_data", ""),
            stroke_data,
        )

        # Fetch all combined strokes and broadcast updated shared canvas to ALL players
        drawings = await self._drawing_service.get_round_drawings(game.id, game.current_round)
        combined_strokes = []
        for d in drawings:
            if d.get("stroke_data"):
                combined_strokes.extend(d["stroke_data"])
        logger.info("[CANVAS_UPDATED] Broadcasting shared canvas with %d total strokes in %s",
                    len(combined_strokes), room_code)
        await self.manager.broadcast_to_room(
            room_code,
            {
                "type": "canvas_updated",
                "data": {"strokes": combined_strokes},
            },
        )

        await self.manager.send_to_player(
            room_code, player_id,
            {"type": "drawing_confirmed", "data": {"success": True}},
        )

        await self.stop_timer(room_code + "_phase")
        self._current_turn_idx[room_code] = current_idx + 1
        await self._advance_turn(room_code, game)

    async def handle_vote_submit(self, room_code: str, player_id: str, data: dict[str, Any]) -> None:
        player = await self._player_repo.get_by_id(uuid.UUID(player_id))
        if not player:
            raise ValueError("Player not found")

        game = await self._game_repo.get_by_room(player.room_id)
        if not game or game.current_phase != GamePhase.VOTING.value:
            raise ValueError("Not in voting phase")

        target_id = data.get("target_player_id")
        if not target_id:
            raise ValueError("target_player_id is required")

        await self._vote_service.submit_vote(game, player, uuid.UUID(target_id))
        logger.info("[VOTE] Player %s voted — room=%s", player_id, room_code)

        # Broadcast updated vote counts so clients see progress
        votes_in = await self._vote_service.get_current_round_vote_count(game.id)
        active_count = await self._vote_service.get_active_player_count(game.id)
        logger.info("[VOTE] Votes: %d / %d in %s", votes_in, active_count, room_code)

        await self.manager.broadcast_to_room(
            room_code,
            {
                "type": "vote_progress",
                "data": {
                    "votes_received": votes_in,
                    "total_expected": active_count,
                },
            },
        )

        await self.manager.send_to_player(
            room_code, player_id,
            {"type": "vote_confirmed", "data": {"success": True}},
        )

        everyone_voted = await self._vote_service.has_everyone_voted(game.id)
        if everyone_voted:
            logger.info("[VOTE] Voting complete — all %d players voted in %s", active_count, room_code)
            # Refresh game from DB to get the latest state
            fresh_game = await self._game_repo.get_by_id(game.id)
            if fresh_game:
                game = fresh_game
            await self._resolve_round(room_code, game)

    async def _resolve_round(self, room_code: str, game) -> None:
        # Guard: prevent double-processing the same room+round
        current_round = game.current_round
        if self._voting_resolved.get(room_code) == current_round:
            logger.info("[VOTE] _resolve_round already processed round %d in %s, skipping", current_round, room_code)
            return
        self._voting_resolved[room_code] = current_round

        await self.stop_timer(room_code + "_vote_countdown")
        await self.stop_timer(room_code + "_vote_timeout")

        # Fetch a fresh game object — the stale one has old phase/round
        fresh_game = await self._game_repo.update_phase(game.id, GamePhase.RESULTS.value)
        if not fresh_game:
            logger.error("[RESULT] Failed to update phase to RESULTS for %s", room_code)
            return
        logger.info("[PHASE] RESULTS — room=%s", room_code)

        # Fetch the persisted round record for authoritative category, word, and imposter_id
        round_record = await self._game_repo.get_round(fresh_game.id, fresh_game.current_round)
        round_category = round_record.category if round_record else None
        round_word = round_record.word if round_record else None
        persisted_imposter_id = round_record.imposter_id if round_record else None
        logger.info("[RESULT] round=%d game=%s imposter_id=%s word='%s' category='%s'",
                    fresh_game.current_round, fresh_game.id, persisted_imposter_id,
                    round_word, round_category)

        results = await self._vote_service.get_vote_results(fresh_game.id, round_number=fresh_game.current_round)
        logger.info("[RESULT] Vote results for %s: %s", room_code, results)

        game_result = await self._game_service.calculate_results(fresh_game)
        logger.info("[RESULT] Game result for %s: winner=%s", room_code, game_result.get("winner"))

        players = await self._player_repo.get_by_room(fresh_game.room_id)

        # SOLE source of truth: the round.imposter_id persisted when the round started.
        # NEVER fall back to player.is_imposter — that flag is re-assigned every round.
        if not persisted_imposter_id:
            logger.error("[RESULT] CRITICAL: round %d has no persisted imposter_id! game=%s",
                         fresh_game.current_round, fresh_game.id)
        imposter = next((p for p in players if persisted_imposter_id and p.id == persisted_imposter_id), None)
        imposter_id_str = str(imposter.id) if imposter else str(persisted_imposter_id) if persisted_imposter_id else ""
        imposter_nickname_str = imposter.nickname if imposter else "Unknown"

        scores = [
            {"player_id": str(p.id), "nickname": p.nickname, "score": p.score}
            for p in players
        ]

        # Build vote breakdown with player nicknames
        vote_details = []
        voter_map = results.get("voter_map", {})
        for voter_id_str, target_id_str in voter_map.items():
            voter = next((p for p in players if str(p.id) == voter_id_str), None)
            target = next((p for p in players if str(p.id) == target_id_str), None)
            if voter and target:
                vote_details.append({
                    "voter_id": voter_id_str,
                    "voter_nickname": voter.nickname,
                    "target_id": target_id_str,
                    "target_nickname": target.nickname,
                })

        await self._broadcast_game_state(
            room_code, fresh_game,
            timer_remaining=0,
            timer_phase="results",
        )
        await self.manager.broadcast_to_room(
            room_code,
            {
                "type": "phase_change",
                "data": {"phase": "results"},
            },
        )
        await self.manager.broadcast_to_room(
            room_code,
            {
                "type": "round_results",
                "data": {
                    "results": results,
                    "game_result": {
                        "winner": game_result.get("winner", "innocent"),
                        "imposter_id": imposter_id_str,
                        "imposter_nickname": imposter_nickname_str,
                        "scores": scores,
                        "category": round_category,
                        "word": round_word,
                        "vote_details": vote_details,
                    },
                    "round": fresh_game.current_round,
                },
            },
        )

        room = await self._room_repo.get_by_id(fresh_game.room_id)
        logger.info("[ROUND_COMPLETED] Round %d/%d finished in %s — winner=%s",
                    fresh_game.current_round, room.num_rounds, room_code, game_result.get("winner"))
        if fresh_game.current_round >= room.num_rounds:
            await self._game_repo.end_game(fresh_game.id)
            self._game_service.clear_word_history(fresh_game.id)
            logger.info("[GAME_OVER] Final round completed in %s", room_code)
            await asyncio.sleep(2)
            await self._broadcast_game_state(
                room_code, fresh_game,
                timer_remaining=0,
                timer_phase="game_over",
            )
            await self.manager.broadcast_to_room(
                room_code,
                {"type": "phase_change", "data": {"phase": "game_over"}},
            )
        else:
            # Don't auto-advance: host must click Next Round
            logger.info("[ROUND_ENDED] Waiting for host to start next round in %s", room_code)
            await self._broadcast_game_state(
                room_code, fresh_game,
                timer_remaining=0,
                timer_phase="round_ended",
            )
            await self.manager.broadcast_to_room(
                room_code,
                {
                    "type": "round_ended",
                    "data": {
                        "round": fresh_game.current_round,
                        "total_rounds": room.num_rounds,
                    },
                },
            )

    async def handle_chat(self, room_code: str, player_id: str, data: dict[str, Any]) -> None:
        player = await self._player_repo.get_by_id(uuid.UUID(player_id))
        if not player:
            raise ValueError("Player not found")

        game = await self._game_repo.get_by_room(player.room_id)
        if not game:
            raise ValueError("Game not found")

        message_text = data.get("text", "") or data.get("message", "")

        await self.manager.broadcast_to_room(
            room_code,
            {
                "type": "chat_message",
                "data": {
                    "player_id": str(player.id),
                    "nickname": player.nickname,
                    "text": message_text,
                    "timestamp": asyncio.get_event_loop().time(),
                },
            },
        )

    async def handle_disconnect(self, room_code: str, player_id: str, data: dict[str, Any] | None = None, websocket=None) -> None:
        removed = self.manager.disconnect(room_code, player_id, websocket=websocket)
        if not removed:
            logger.info("[DISCONNECT] Player %s socket was stale (newer connection exists) in %s, skipping cleanup", player_id, room_code)
            return

        try:
            player = await self._player_repo.get_by_id(uuid.UUID(player_id))
            if not player:
                return

            was_host = player.is_host
            room = await self._room_repo.get_by_code(room_code)
            await self._player_repo.set_connected(uuid.UUID(player_id), False)
            logger.info("[DISCONNECT] Player %s disconnected from %s (was_host=%s)", player_id, room_code, was_host)

            # If host disconnected, transfer to longest-connected player
            if was_host and room:
                remaining = await self._player_repo.get_by_room(room.id)
                connected = [p for p in remaining if p.is_connected and str(p.id) != player_id]
                if connected:
                    new_host = connected[0]  # sorted by created_at ASC
                    await self._player_repo.transfer_host(room.id, new_host.id)
                    logger.info("[HOST_TRANSFER] Disconnect: host transferred to %s (%s) — longest-connected",
                                new_host.nickname, new_host.id)
                    await self.manager.broadcast_to_room(
                        room_code,
                        {"type": "host_changed", "data": {"host_id": str(new_host.id)}},
                    )

            game = await self._game_repo.get_by_room(player.room_id)

            # Start a 25-second grace period before ending game
            if game:
                async def _disconnect_timeout() -> None:
                    await asyncio.sleep(25)
                    # Check if player reconnected
                    p = await self._player_repo.get_by_id(uuid.UUID(player_id))
                    if p and not p.is_connected:
                        logger.info("[DISCONNECT_TIMEOUT] Player %s did not reconnect within 25s, evaluating game end", player_id)
                        try:
                            result = await self._game_service.handle_disconnect(game, uuid.UUID(player_id))
                        except Exception as e:
                            logger.error("[DISCONNECT_TIMEOUT] handle_disconnect crashed for %s: %s", player_id, e)
                            result = {"action": "none"}
                        if result.get("action") == "end_game":
                            logger.info("[GAME] Ending game in %s — not enough players after disconnect timeout", room_code)
                            if game:
                                self._game_service.clear_word_history(game.id)
                            await self.manager.broadcast_to_room(
                                room_code,
                                {"type": "game_over", "data": {"reason": "not_enough_players"}},
                            )
                            await self.manager.disconnect_all(room_code)

                    self._disconnect_timers.pop(player_id, None)

                timer = asyncio.create_task(_disconnect_timeout())
                self._disconnect_timers[player_id] = timer
                logger.info("[DISCONNECT] Started 25s reconnect timer for %s in %s", player_id, room_code)

            await self._broadcast_room(room_code)
        except Exception as e:
            logger.error("[DISCONNECT] Error during disconnect cleanup for %s in %s: %s", player_id, room_code, e)

    async def handle_update_settings(self, room_code: str, player_id: str, data: dict[str, Any]) -> None:
        player = await self._player_repo.get_by_id(uuid.UUID(player_id))
        if not player or not player.is_host:
            raise ValueError("Only the host can update settings")

        room = await self._room_repo.get_by_code(room_code)
        if not room:
            raise ValueError("Room not found")

        updatable = {}
        for key in ("max_players", "num_rounds", "drawing_time", "voting_time", "num_imposters", "word_category", "difficulty"):
            if key in data:
                updatable[key] = data[key]

        if updatable:
            await self._room_repo.update_settings(room.id, **updatable)

        logger.info("[SETTINGS] Updated in %s: %s", room_code, updatable)
        await self._broadcast_room(room_code)

    async def handle_kick_player(self, room_code: str, player_id: str, data: dict[str, Any]) -> None:
        player = await self._player_repo.get_by_id(uuid.UUID(player_id))
        if not player or not player.is_host:
            raise ValueError("Only the host can kick players")

        target_id = data.get("player_id")
        if not target_id:
            raise ValueError("player_id is required")

        if target_id == player_id:
            raise ValueError("The host cannot kick themselves")

        target = await self._player_repo.get_by_id(uuid.UUID(target_id))
        if not target:
            raise ValueError("Player not found")

        # Cannot kick after the game has started
        game = await self._game_repo.get_by_room(player.room_id)
        if game and game.current_phase and game.current_phase != "lobby":
            raise ValueError("Cannot kick players after the game has started")

        target_nickname = target.nickname

        # Send kick message BEFORE disconnecting (so it actually reaches them)
        await self.manager.send_to_player(
            room_code, target_id,
            {"type": "kick", "data": {"message": "You were removed from the room by the host."}},
        )

        # Remove from database
        await self._player_repo.kick(uuid.UUID(target_id))

        # Close their WebSocket connection cleanly
        ws = self.manager.active_connections.get(room_code, {}).get(target_id)
        if ws:
            try:
                await ws.close(code=1000)
            except Exception:
                pass
        self.manager.disconnect(room_code, target_id)

        logger.info("[KICK] Player %s (%s) kicked by %s from %s", target_id, target_nickname, player_id, room_code)

        # Notify remaining players who was kicked
        await self.manager.broadcast_to_room(
            room_code,
            {"type": "player_kicked", "data": {"player_id": target_id, "nickname": target_nickname}},
            exclude=[target_id],
        )

        room = await self._room_repo.get_by_code(room_code)
        if room:
            remaining = await self._player_repo.get_by_room(room.id)
            if not remaining:
                logger.info("[ROOM] Room %s is now empty, deleting", room_code)
                await self._room_repo.delete(room.id)
                await self.manager.disconnect_all(room_code)
                return

        await self._broadcast_room(room_code)

    async def handle_next_round(self, room_code: str, player_id: str, data: dict[str, Any]) -> None:
        player = await self._player_repo.get_by_id(uuid.UUID(player_id))
        if not player or not player.is_host:
            raise ValueError("Only the host can start the next round")

        game = await self._game_repo.get_by_room(player.room_id)
        if not game:
            raise ValueError("Game not found")

        room = await self._room_repo.get_by_code(room_code)
        if not room:
            raise ValueError("Room not found")

        word, category = await self._game_service.select_word(game, room.word_category, room.difficulty)

        players_updated = await self._player_repo.get_by_room(room.id)
        updated_assigned = await self._game_service.assign_roles(game, players_updated, room.num_imposters)
        imposter_ids = [p.id for p in updated_assigned if p.is_imposter]

        game = await self._game_service.start_next_round(game, imposter_ids)

        turn_order = [str(p.id) for p in players_updated if p.is_connected]
        random.shuffle(turn_order)
        self._turn_order[room_code] = turn_order
        self._current_turn_idx[room_code] = 0

        logger.info("[NEXT_ROUND] Host %s started round %d in %s — turn_order=%s",
                    player_id, game.current_round, room_code, turn_order)

        await self._broadcast_game_state(
            room_code, game,
            timer_remaining=0,
            timer_phase="assign_roles",
        )
        await self.manager.broadcast_to_room(
            room_code,
            {
                "type": "round_start",
                "data": {"round": game.current_round, "total_rounds": room.num_rounds},
            },
        )

        for p in players_updated:
            if p.is_imposter:
                await self.manager.send_to_player(
                    room_code, str(p.id),
                    {
                        "type": "word_assigned",
                        "data": {
                            "word_hint": None,
                            "category": category,
                            "is_imposter": True,
                            "role": "imposter",
                            "message": "You are the Imposter. You do not know today's word. Try to blend in.",
                        },
                    },
                )
            else:
                await self.manager.send_to_player(
                    room_code, str(p.id),
                    {
                        "type": "word_assigned",
                        "data": {
                            "word_hint": word,
                            "category": category,
                            "is_imposter": False,
                            "role": "artist",
                        },
                    },
                )

        await self._advance_turn(room_code, game)

    async def handle_play_again(self, room_code: str, player_id: str, data: dict[str, Any]) -> None:
        player = await self._player_repo.get_by_id(uuid.UUID(player_id))
        if not player:
            raise ValueError("Player not found")

        room = await self._room_repo.get_by_code(room_code)
        if not room:
            raise ValueError("Room not found")

        # Clear the old game's word history to allow full reuse in the new game
        game = await self._game_repo.get_by_room(room.id)
        if game:
            self._game_service.clear_word_history(game.id)

        await self._room_repo.update_status(room.id, "waiting")
        players = await self._player_repo.get_by_room(room.id)
        for p in players:
            await self._player_repo.update_score(p.id, 0)
            await self._player_repo.update_ready(p.id, False)

        self._turn_order.pop(room_code, None)
        self._current_turn_idx.pop(room_code, None)

        logger.info("[PLAY_AGAIN] Room %s reset for new game", room_code)
        await self.manager.broadcast_to_room(room_code, {
            "type": "phase_change",
            "data": {"phase": "lobby"},
        })
        await self._broadcast_room(room_code)

    def start_timer(self, room_code: str, phase: str, duration: int) -> asyncio.Task:
        async def _timer() -> None:
            remaining = duration
            while remaining > 0:
                await self.manager.broadcast_to_room(
                    room_code,
                    {"type": "timer_sync", "data": {"phase": phase, "time_remaining": remaining}},
                )
                await asyncio.sleep(1)
                remaining -= 1
            await self.manager.broadcast_to_room(
                room_code,
                {"type": "timer_end", "data": {"phase": phase}},
            )

        task = asyncio.create_task(_timer())
        return task

    async def stop_timer(self, timer_key: str) -> None:
        entry = self._timers.get(timer_key)
        if entry is not None:
            entry.cancel()
            del self._timers[timer_key]
