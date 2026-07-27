import { create } from 'zustand';
import type { Player, RoomSettings, GamePhase, ChatMessage, RoundResult, GameResult, DrawingData, CanvasStroke } from '../types';

interface GameStore {
  // Player
  playerId: string | null;
  nickname: string | null;
  setPlayer: (id: string, nickname: string) => void;

  // Room
  roomCode: string | null;
  roomName: string | null;
  players: Player[];
  settings: RoomSettings | null;
  isHost: boolean;
  setRoom: (code: string, name: string, settings: RoomSettings) => void;
  setPlayers: (players: Player[]) => void;
  addPlayer: (player: Player) => void;
  removePlayer: (playerId: string) => void;
  updatePlayerReady: (playerId: string, isReady: boolean) => void;
  setHost: (isHost: boolean) => void;

  // Game
  phase: GamePhase;
  currentRound: number;
  totalRounds: number;
  wordHint: string | null;
  timeRemaining: number;
  isImposter: boolean;
  hasVoted: boolean;
  drawingSubmitted: boolean;
  currentTurnPlayerId: string | null;
  setPhase: (phase: GamePhase) => void;
  setGameState: (state: Partial<GameStore>) => void;
  setTimeRemaining: (time: number) => void;
  setWordHint: (hint: string | null) => void;
  setIsImposter: (is: boolean) => void;
  setHasVoted: (voted: boolean) => void;
  setDrawingSubmitted: (submitted: boolean) => void;
  setCurrentRound: (round: number) => void;
  setCurrentTurnPlayerId: (playerId: string | null) => void;
  setTotalRounds: (total: number) => void;

  // Reveal & Results
  revealDrawings: DrawingData[];
  roundResults: RoundResult[];
  gameResult: GameResult | null;
  setRevealDrawings: (drawings: DrawingData[]) => void;
  setRoundResults: (results: RoundResult[]) => void;
  setGameResult: (result: GameResult | null) => void;

  // Shared canvas strokes (all strokes for current round, in order)
  roundStrokes: CanvasStroke[];
  awaitingNextRound: boolean;
  setRoundStrokes: (strokes: CanvasStroke[]) => void;
  addRoundStroke: (stroke: CanvasStroke) => void;
  setAwaitingNextRound: (waiting: boolean) => void;

  // Chat
  chatMessages: ChatMessage[];
  addChatMessage: (msg: ChatMessage) => void;
  clearChat: () => void;

  // Connection
  isConnected: boolean;
  error: string | null;
  setConnected: (connected: boolean) => void;
  setError: (error: string | null) => void;

  // Actions
  reset: () => void;
}

const initialState = {
  playerId: null,
  nickname: null,
  roomCode: null,
  roomName: null,
  players: [],
  settings: null,
  isHost: false,
  phase: 'lobby' as GamePhase,
  currentRound: 0,
  totalRounds: 0,
  wordHint: null,
  timeRemaining: 0,
  isImposter: false,
  hasVoted: false,
  drawingSubmitted: false,
  currentTurnPlayerId: null,
  roundStrokes: [],
  awaitingNextRound: false,
  revealDrawings: [],
  roundResults: [],
  gameResult: null,
  chatMessages: [],
  isConnected: false,
  error: null,
};

export const useGameStore = create<GameStore>((set) => ({
  ...initialState,

  setPlayer: (id, nickname) => set({ playerId: id, nickname }),
  setRoom: (code, name, settings) => set({ roomCode: code, roomName: name, settings }),
  setPlayers: (players) => set({ players }),
  addPlayer: (player) => set((s) => ({ players: [...s.players.filter((p) => p.id !== player.id), player] })),
  removePlayer: (playerId) => set((s) => ({ players: s.players.filter((p) => p.id !== playerId) })),
  updatePlayerReady: (playerId, isReady) => set((s) => ({
    players: s.players.map((p) => (p.id === playerId ? { ...p, is_ready: isReady } : p)),
  })),
  setHost: (isHost) => set({ isHost }),

  setPhase: (phase) => set({ phase }),
  setGameState: (state) => set(state),
  setTimeRemaining: (time) => set({ timeRemaining: time }),
  setWordHint: (hint) => set({ wordHint: hint }),
  setIsImposter: (is) => set({ isImposter: is }),
  setHasVoted: (voted) => set({ hasVoted: voted }),
  setDrawingSubmitted: (submitted) => set({ drawingSubmitted: submitted }),
  setCurrentRound: (round) => set({ currentRound: round }),
  setCurrentTurnPlayerId: (playerId) => set({ currentTurnPlayerId: playerId }),
  setTotalRounds: (total) => set({ totalRounds: total }),

  setRoundStrokes: (strokes) => set({ roundStrokes: strokes }),
  addRoundStroke: (stroke) => set((s) => ({ roundStrokes: [...s.roundStrokes, stroke] })),
  setAwaitingNextRound: (waiting) => set({ awaitingNextRound: waiting }),

  setRevealDrawings: (drawings) => set({ revealDrawings: drawings }),
  setRoundResults: (results) => set({ roundResults: results }),
  setGameResult: (result) => set({ gameResult: result }),

  addChatMessage: (msg) => set((s) => ({ chatMessages: [...s.chatMessages, msg] })),
  clearChat: () => set({ chatMessages: [] }),

  setConnected: (connected) => set({ isConnected: connected }),
  setError: (error) => set({ error }),

  reset: () => set(initialState),
}));
