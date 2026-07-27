export const WS_BASE_URL = import.meta.env.VITE_WS_URL || `ws://${window.location.hostname}:8000`;
export const API_BASE_URL = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000`;
export const MAX_PLAYERS = 8;
export const MIN_PLAYERS = 3;
export const DEFAULT_SETTINGS = {
  max_players: 8,
  num_rounds: 3,
  drawing_time: 60,
  voting_time: 30,
  num_imposters: 1,
  word_category: null,
  difficulty: 'medium',
};
export const AVATAR_COLORS = [
  '#6366f1', '#ef4444', '#22c55e', '#f59e0b',
  '#8b5cf6', '#ec4899', '#06b6d4', '#f97316',
];
export const CANVAS_COLORS = ['#000000', '#ffffff', '#ef4444', '#f59e0b', '#22c55e', '#3b82f6', '#8b5cf6', '#ec4899'];
