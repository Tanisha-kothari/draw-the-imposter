export type GamePhase = 'lobby' | 'ready' | 'assign_roles' | 'drawing' | 'reveal' | 'voting' | 'results' | 'game_over';

export interface Player {
  id: string;
  nickname: string;
  score: number;
  is_ready: boolean;
  is_host: boolean;
  is_connected: boolean;
  is_imposter?: boolean;
  avatar_color?: string;
}

export interface RoomSettings {
  max_players: number;
  num_rounds: number;
  drawing_time: number;
  voting_time: number;
  num_imposters: number;
  word_category: string | null;
  difficulty: string;
}

export interface Room {
  id: string;
  code: string;
  name: string;
  host_id: string;
  players: Player[];
  settings: RoomSettings;
  status: string;
}

export interface GameState {
  phase: GamePhase;
  current_round: number;
  total_rounds: number;
  word_hint: string | null;
  time_remaining: number;
  players: Player[];
  is_imposter: boolean;
  has_voted: boolean;
  drawing_submitted: boolean;
}

export interface DrawingData {
  id?: string;
  player_id: string;
  nickname: string;
  player_number: number;
  image_data: string;
  stroke_data?: any;
  round_number: number;
}

export interface VoteResult {
  player_id: string;
  player_nickname: string;
  vote_count: number;
}

export interface RoundResult {
  round: number;
  word: string;
  drawings: DrawingData[];
  votes: VoteResult[];
  imposter_id: string;
  correct_guess: boolean;
}

export interface GameResult {
  winner: 'imposter' | 'innocent';
  imposter_id: string;
  imposter_nickname: string;
  scores: { player_id: string; nickname: string; score: number }[];
  round_results: RoundResult[];
}

// WebSocket message types
export interface WSMessage {
  type: string;
  data: Record<string, unknown>;
  timestamp?: number;
}

export interface ChatMessage {
  player_id: string;
  nickname: string;
  text: string;
  timestamp: number;
}

export interface CanvasStroke {
  tool: 'pencil' | 'eraser';
  color: string;
  size: number;
  points: { x: number; y: number; pressure?: number }[];
}
