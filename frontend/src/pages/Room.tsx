import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useGameStore } from '../store/gameStore';
import { useUIStore } from '../store/uiStore';
import { useWebSocket } from '../hooks/useWebSocket';
import { api } from '../lib/api';
import Button from '../components/ui/Button';
import Avatar from '../components/ui/Avatar';
import Modal from '../components/ui/Modal';

export default function Room() {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();
  const playerId = useGameStore((s) => s.playerId);
  const { sendMessage } = useWebSocket(code || null, playerId);

  const players = useGameStore((s) => s.players);
  const isHost = useGameStore((s) => s.isHost);
  const settings = useGameStore((s) => s.settings);
  const roomCode = useGameStore((s) => s.roomCode);
  const phase = useGameStore((s) => s.phase);
  const setPlayers = useGameStore((s) => s.setPlayers);
  const setRoom = useGameStore((s) => s.setRoom);
  const isConnected = useGameStore((s) => s.isConnected);
  const addToast = useUIStore((s) => s.addToast);

  const [showSettings, setShowSettings] = useState(false);
  const [localSettings, setLocalSettings] = useState(settings);
  const [copied, setCopied] = useState(false);
  const [confirmKick, setConfirmKick] = useState<{ id: string; nickname: string } | null>(null);

  useEffect(() => {
    if (!code || !playerId) {
      navigate('/');
      return;
    }
    api.getRoom(code).then((res: any) => {
      setPlayers(res.players || []);
      setRoom(res.code, res.name, res.settings);
    }).catch(() => navigate('/'));
  }, [code, playerId]);

  useEffect(() => {
    if (settings) setLocalSettings(settings);
  }, [settings]);

  useEffect(() => {
    if (phase && phase !== 'lobby') {
      navigate(`/game/${code}`);
    }
  }, [phase, code, navigate]);

  const myPlayer = players.find((p) => p.id === playerId);
  const isReady = myPlayer?.is_ready ?? false;

  const handleReady = useCallback(() => {
    sendMessage('ready', { is_ready: !isReady });
  }, [sendMessage, isReady]);

  const handleStart = useCallback(() => {
    sendMessage('start_game', {});
  }, [sendMessage]);

  const handleKick = useCallback((targetId: string) => {
    sendMessage('kick_player', { player_id: targetId });
    setConfirmKick(null);
  }, [sendMessage]);

  const handleCopyCode = () => {
    if (roomCode) {
      navigator.clipboard.writeText(roomCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleSaveSettings = () => {
    if (!isHost || !localSettings) return;
    sendMessage('update_settings', localSettings as any);
    setShowSettings(false);
    addToast('Settings updated', 'success');
  };

  if (!code || !settings) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4 md:p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold">Game Lobby</h1>
            <p className="text-gray-400 text-sm">{players.length} / {settings.max_players} players</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 bg-gray-900 px-4 py-2 rounded-xl border border-gray-800">
              <span className="text-sm text-gray-400">Room:</span>
              <span className="font-mono font-bold text-lg tracking-widest text-primary-400">{roomCode}</span>
              <button onClick={handleCopyCode} className="p-1 hover:bg-gray-800 rounded transition-colors">
                {copied ? (
                  <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                )}
              </button>
            </div>
            {!isConnected && (
              <span className="text-red-400 text-sm animate-pulse">Disconnected</span>
            )}
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <div className="card">
              <h2 className="text-lg font-semibold mb-4">Players</h2>
              <div className="space-y-2">
                {players.map((player, idx) => (
                  <div
                    key={player.id}
                    className="flex items-center justify-between p-3 rounded-xl bg-gray-800/50 hover:bg-gray-800 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <Avatar
                        nickname={player.nickname}
                        colorIndex={idx}
                        isHost={player.is_host}
                        isReady={player.is_ready}
                        size="md"
                      />
                      <div>
                        <span className="font-medium">{player.nickname}</span>
                        {player.id === playerId && (
                          <span className="text-xs text-gray-500 ml-2">(You)</span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {player.is_ready && (
                        <span className="text-xs bg-green-600/20 text-green-400 px-2 py-1 rounded-full font-medium">Ready</span>
                      )}
                      {isHost && player.id !== playerId && (
                        <button
                          onClick={() => setConfirmKick({ id: player.id, nickname: player.nickname })}
                          className="p-1.5 text-gray-500 hover:text-red-400 hover:bg-red-600/20 rounded-lg transition-all"
                          title="Kick"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      )}
                    </div>
                  </div>
                ))}
                {players.length === 0 && (
                  <p className="text-gray-500 text-center py-8">Waiting for players...</p>
                )}
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="card">
              <h2 className="text-lg font-semibold mb-4">Controls</h2>
              {isHost ? (
                <div className="space-y-3">
                  <Button className="w-full" variant="secondary" onClick={() => setShowSettings(true)}>
                    Game Settings
                  </Button>
                  <Button
                    className="w-full"
                    onClick={handleStart}
                    disabled={players.length < 2 || !players.every((p) => p.is_ready || p.is_host)}
                  >
                    Start Game
                  </Button>
                  {players.length < 2 && (
                    <p className="text-xs text-gray-500 text-center">Need at least 2 players</p>
                  )}
                </div>
              ) : (
                <Button className="w-full" onClick={handleReady}>
                  {isReady ? 'Not Ready' : 'Ready'}
                </Button>
              )}
            </div>

            {isHost && (
              <div className="card">
                <h3 className="text-sm font-semibold text-gray-400 mb-2">Quick Settings</h3>
                <div className="space-y-2 text-sm text-gray-400">
                  <p>Rounds: {settings.num_rounds}</p>
                  <p>Draw Time: {settings.drawing_time}s</p>
                  <p>Vote Time: {settings.voting_time}s</p>
                  <p>Imposters: {settings.num_imposters}</p>
                  <p>Max Players: {settings.max_players}</p>
                </div>
              </div>
            )}
          </div>
        </div>

        <Modal isOpen={showSettings} onClose={() => setShowSettings(false)} title="Game Settings" size="md">
          {localSettings && (
            <div className="space-y-4">
              {[
                { key: 'num_rounds', label: 'Rounds', min: 1, max: 5 },
                { key: 'drawing_time', label: 'Drawing Time (s)', min: 10, max: 120, step: 5 },
                { key: 'voting_time', label: 'Voting Time (s)', min: 10, max: 60, step: 5 },
                { key: 'num_imposters', label: 'Imposters', min: 1, max: Math.max(1, Math.floor(players.length / 2)) },
                { key: 'max_players', label: 'Max Players', min: 3, max: 8 },
              ].map(({ key, label, min, max, step }) => (
                <div key={key}>
                  <label className="block text-sm font-medium text-gray-300 mb-1">{label}: {localSettings[key as keyof typeof localSettings]}</label>
                  <input
                    type="range"
                    min={min}
                    max={max}
                    step={step || 1}
                    value={localSettings[key as keyof typeof localSettings] as number}
                    onChange={(e) => setLocalSettings({ ...localSettings, [key]: parseInt(e.target.value) })}
                    className="w-full accent-primary-500"
                  />
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>{min}</span>
                    <span>{max}</span>
                  </div>
                </div>
              ))}
              <div className="flex gap-3 pt-2">
                <Button variant="secondary" className="flex-1" onClick={() => setShowSettings(false)}>Cancel</Button>
                <Button className="flex-1" onClick={handleSaveSettings}>Save</Button>
              </div>
            </div>
          )}
        </Modal>

        <Modal isOpen={confirmKick !== null} onClose={() => setConfirmKick(null)} title="Kick Player" size="sm">
          {confirmKick && (
            <div className="space-y-4">
              <p className="text-gray-300">Remove <span className="font-semibold text-white">{confirmKick.nickname}</span> from the room?</p>
              <div className="flex gap-3 pt-2">
                <Button variant="secondary" className="flex-1" onClick={() => setConfirmKick(null)}>Cancel</Button>
                <Button className="flex-1" onClick={() => handleKick(confirmKick.id)}>Remove</Button>
              </div>
            </div>
          )}
        </Modal>
      </div>
    </div>
  );
}
