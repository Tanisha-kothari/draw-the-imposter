import { API_BASE_URL } from './constants';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) throw new Error(`API Error: ${res.status} ${res.statusText}`);
  return res.json();
}

import type { RoomSettings } from '../types';

interface RoomCreateResponse {
  code: string;
  room_name: string;
  room_id: string;
  player_id: string;
  is_host: boolean;
  settings: RoomSettings;
}

interface RoomResponse {
  code: string;
  name: string;
  settings: RoomSettings;
  players: Record<string, unknown>[];
  status: string;
}

export const api = {
  createRoom: (data: Record<string, unknown>): Promise<RoomCreateResponse> =>
    request('/api/rooms', { method: 'POST', body: JSON.stringify(data) }),
  joinRoom: (data: { code: string; nickname: string }): Promise<RoomCreateResponse> =>
    request('/api/rooms/join', { method: 'POST', body: JSON.stringify(data) }),
  getRoom: (code: string): Promise<RoomResponse> =>
    request(`/api/rooms/${code}`),
  updateSettings: (code: string, data: Record<string, unknown>) =>
    request(`/api/rooms/${code}/settings`, { method: 'PUT', body: JSON.stringify(data) }),
  kickPlayer: (code: string, data: { player_id: string }) =>
    request(`/api/rooms/${code}/kick`, { method: 'POST', body: JSON.stringify(data) }),
  healthCheck: (): Promise<{ status: string }> => request('/health'),
};
