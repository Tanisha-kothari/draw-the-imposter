import { useEffect, useRef, useCallback } from 'react';
import { useGameStore } from '../store/gameStore';
import { useUIStore } from '../store/uiStore';
import { WS_BASE_URL } from '../lib/constants';
import type { WSMessage, ChatMessage, CanvasStroke } from '../types';

const MAX_RECONNECT_ATTEMPTS = 5;

let socketCounter = 0;

export function useWebSocket(roomCode: string | null, playerId: string | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptRef = useRef(0);
  const reconnectTimerRef = useRef<number | null>(null);
  const pingIntervalRef = useRef<number | null>(null);
  const disposedRef = useRef(false);
  const socketIdRef = useRef<number | null>(null);

  const setConnected = useGameStore((s) => s.setConnected);
  const setPlayers = useGameStore((s) => s.setPlayers);
  const addPlayer = useGameStore((s) => s.addPlayer);
  const removePlayer = useGameStore((s) => s.removePlayer);
  const updatePlayerReady = useGameStore((s) => s.updatePlayerReady);
  const setPhase = useGameStore((s) => s.setPhase);
  const setGameState = useGameStore((s) => s.setGameState);
  const setTimeRemaining = useGameStore((s) => s.setTimeRemaining);
  const setWordHint = useGameStore((s) => s.setWordHint);
  const setWordCategory = useGameStore((s) => s.setWordCategory);
  const setIsImposter = useGameStore((s) => s.setIsImposter);
  const setHasVoted = useGameStore((s) => s.setHasVoted);
  const setDrawingSubmitted = useGameStore((s) => s.setDrawingSubmitted);
  const setCurrentRound = useGameStore((s) => s.setCurrentRound);
  const setCurrentTurnPlayerId = useGameStore((s) => s.setCurrentTurnPlayerId);
  const setTotalRounds = useGameStore((s) => s.setTotalRounds);
  const setRevealDrawings = useGameStore((s) => s.setRevealDrawings);
  const setRoundResults = useGameStore((s) => s.setRoundResults);
  const setGameResult = useGameStore((s) => s.setGameResult);
  const setRoundStrokes = useGameStore((s) => s.setRoundStrokes);
  const setAwaitingNextRound = useGameStore((s) => s.setAwaitingNextRound);
  const addChatMessage = useGameStore((s) => s.addChatMessage);
  const setHost = useGameStore((s) => s.setHost);
  const setError = useGameStore((s) => s.setError);
  const addToast = useUIStore((s) => s.addToast);
  const setLoading = useUIStore((s) => s.setLoading);

  const handleMessage = useCallback((msg: WSMessage) => {
    const data = msg.data || {};
    const localPlayerId = useGameStore.getState().playerId;
    switch (msg.type) {
      case 'game_state':
        setGameState(data);
        break;
      case 'room_updated':
        if (data.players) setPlayers(data.players as any[]);
        if (data.settings) useGameStore.getState().setRoom(data.code as string, data.room_name as string, data.settings as any);
        if (data.host_id) setHost(data.host_id === localPlayerId);
        break;
      case 'player_joined':
        addPlayer(data as any);
        break;
      case 'player_left':
        removePlayer(data.player_id as string);
        break;
      case 'player_ready':
        updatePlayerReady(data.player_id as string, data.is_ready as boolean);
        break;
      case 'players_list':
        setPlayers(data.players as any[]);
        break;
      case 'game_state_updated':
        // Atomic game state update — single source of truth
        setPhase(data.phase as any);
        setCurrentRound(data.current_round as number);
        setTotalRounds(data.total_rounds as number);
        if (data.current_turn_player_id) {
          setCurrentTurnPlayerId(data.current_turn_player_id as string);
        }
        if (data.timer_remaining !== undefined) {
          setTimeRemaining(data.timer_remaining as number);
        }
        if (data.phase === 'drawing') {
          setDrawingSubmitted(false);
          setHasVoted(false);
          setAwaitingNextRound(false);
        }
        if (data.phase === 'results' || data.phase === 'game_over') {
          setAwaitingNextRound(false);
        }
        break;
      case 'phase_change':
        setPhase(data.phase as any);
        if (data.phase === 'results' || data.phase === 'game_over') {
          setAwaitingNextRound(false);
        }
        break;
      case 'timer_sync': {
        const timerPhase = data.phase as string;
        const currentPhase = useGameStore.getState().phase;
        // Only accept timer updates matching the current game phase
        if (!timerPhase || timerPhase === currentPhase) {
          setTimeRemaining(data.time_remaining as number);
        }
        break;
      }
      case 'timer_end':
        setTimeRemaining(0);
        break;
      case 'word_assigned':
        setWordHint(data.word_hint as string | null);
        setWordCategory(data.category as string | null);
        setIsImposter(data.is_imposter as boolean);
        break;
      case 'round_start':
        setCurrentRound(data.round as number);
        setTotalRounds(data.total_rounds as number);
        setDrawingSubmitted(false);
        setHasVoted(false);
        setCurrentTurnPlayerId(null);
        break;
      case 'turn_change':
        setCurrentTurnPlayerId(data.current_player_id as string);
        if (data.existing_strokes) {
          setRoundStrokes(data.existing_strokes as CanvasStroke[]);
        }
        break;
      case 'reveal_drawings':
        setRevealDrawings(data.drawings as any[]);
        if (data.combined_strokes) {
          setRoundStrokes(data.combined_strokes as CanvasStroke[]);
        }
        break;
      case 'round_results':
        setRoundResults(data.results as any[]);
        setGameResult(data.game_result as any);
        break;
      case 'canvas_updated':
        if (data.strokes) {
          setRoundStrokes(data.strokes as CanvasStroke[]);
        }
        break;
      case 'round_ended':
        setAwaitingNextRound(true);
        break;
      case 'host_changed':
        setHost(data.host_id === localPlayerId);
        addToast('Host has changed', 'info');
        break;
      case 'vote_confirmed':
        setHasVoted(true);
        break;
      case 'drawing_confirmed':
        setDrawingSubmitted(true);
        break;
      case 'chat_message':
        addChatMessage(data as unknown as ChatMessage);
        break;
      case 'error':
        setError(data.message as string);
        addToast(data.message as string, 'error');
        break;
      case 'notification':
        addToast(data.message as string, 'info');
        break;
      case 'kick':
        addToast('You were kicked from the room', 'error');
        window.location.href = '/';
        break;
    }
  }, []);

  const cleanupSocket = useCallback(() => {
    if (reconnectTimerRef.current !== null) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    if (pingIntervalRef.current !== null) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
    if (wsRef.current) {
      const oldSocket = wsRef.current;
      wsRef.current = null;
      try { oldSocket.close(); } catch { /* ignore */ }
    }
  }, []);

  const connect = useCallback(() => {
    if (!roomCode || !playerId) return;

    cleanupSocket();

    const sid = ++socketCounter;
    socketIdRef.current = sid;
    disposedRef.current = false;

    const url = `${WS_BASE_URL}/ws/${roomCode}/${playerId}`;
    console.log(`[WS#${sid}] WebSocket Created → ${url}`);
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      if (disposedRef.current || socketIdRef.current !== sid) {
        console.log(`[WS#${sid}] WebSocket Opened (stale, ignoring)`);
        try { ws.close(); } catch { /* ignore */ }
        return;
      }
      console.log(`[WS#${sid}] WebSocket Connected`);
      setConnected(true);
      reconnectAttemptRef.current = 0;

      pingIntervalRef.current = window.setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, 25000);
    };

    ws.onmessage = (event) => {
      if (disposedRef.current || socketIdRef.current !== sid) return;
      try {
        const message: WSMessage = JSON.parse(event.data);
        console.log(`[WS#${sid}] WebSocket Message: ${message.type}`, message.data);
        handleMessage(message);
      } catch {
        // ignore parse errors
      }
    };

    ws.onclose = (event) => {
      console.log(`[WS#${sid}] WebSocket Closed (code=${event.code})`);
      if (socketIdRef.current === sid) {
        setConnected(false);
      }
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = null;
      }
      if (disposedRef.current) {
        console.log(`[WS#${sid}] Disposed, not reconnecting`);
        return;
      }
      if (socketIdRef.current !== sid) {
        console.log(`[WS#${sid}] Stale close (current=${socketIdRef.current}), not reconnecting`);
        return;
      }
      attemptReconnect();
    };

    ws.onerror = () => {
      console.log(`[WS#${sid}] WebSocket Error`);
    };
  }, [roomCode, playerId, cleanupSocket, handleMessage]);

  const attemptReconnect = useCallback(() => {
    if (disposedRef.current) return;
    if (reconnectAttemptRef.current >= MAX_RECONNECT_ATTEMPTS) {
      console.log(`[WS] Max reconnection attempts reached`);
      setError('Lost connection to server');
      addToast('Unable to reconnect', 'error');
      return;
    }
    reconnectAttemptRef.current++;
    const delay = Math.min(1000 * Math.pow(2, reconnectAttemptRef.current), 16000);
    console.log(`[WS] Reconnecting... (attempt ${reconnectAttemptRef.current}, delay=${delay}ms)`);
    reconnectTimerRef.current = window.setTimeout(connect, delay);
  }, [connect, setError, addToast]);

  const sendMessage = useCallback((type: string, data: Record<string, unknown> = {}) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type, data }));
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      console.log(`[WS] Cleanup triggered for room=${roomCode} player=${playerId}`);
      disposedRef.current = true;
      cleanupSocket();
    };
  }, [connect]);

  const isConnected = useGameStore((s) => s.isConnected);
  return { sendMessage, isConnected };
}
