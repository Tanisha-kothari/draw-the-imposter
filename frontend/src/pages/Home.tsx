import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import Button from '../components/ui/Button';
import { useGameStore } from '../store/gameStore';
import { useUIStore } from '../store/uiStore';

export default function Home() {
  const [joinCode, setJoinCode] = useState('');
  const [nickname, setNickname] = useState('');
  const [loading, setLoading] = useState<'create' | 'join' | null>(null);
  const navigate = useNavigate();
  const setPlayer = useGameStore((s) => s.setPlayer);
  const setRoom = useGameStore((s) => s.setRoom);
  const setHost = useGameStore((s) => s.setHost);
  const addToast = useUIStore((s) => s.addToast);

  const handleCreate = async () => {
    if (!nickname.trim()) { addToast('Enter a nickname', 'error'); return; }
    setLoading('create');
    try {
      const res = await api.createRoom({ nickname: nickname.trim() });
      setPlayer(res.player_id, nickname.trim());
      setRoom(res.code, res.room_name, res.settings);
      setHost(true);
      navigate(`/room/${res.code}`);
    } catch {
      addToast('Failed to create room', 'error');
    } finally { setLoading(null); }
  };

  const handleJoin = async () => {
    if (!nickname.trim() || !joinCode.trim()) { addToast('Enter code and nickname', 'error'); return; }
    setLoading('join');
    try {
      const res = await api.joinRoom({ code: joinCode.trim().toUpperCase(), nickname: nickname.trim() });
      setPlayer(res.player_id, nickname.trim());
      setRoom(res.code, res.room_name, res.settings);
      setHost(res.is_host);
      navigate(`/room/${res.code}`);
    } catch {
      addToast('Failed to join room', 'error');
    } finally { setLoading(null); }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 relative overflow-hidden">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -left-40 w-80 h-80 bg-primary-600/20 rounded-full blur-3xl animate-pulse-slow" />
        <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-purple-600/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1.5s' }} />
      </div>

      <div className="relative z-10 w-full max-w-4xl">
        <div className="text-center mb-12">
          <h1 className="text-5xl md:text-7xl font-black mb-4 bg-gradient-to-r from-primary-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            Draw The Imposter
          </h1>
          <p className="text-xl text-gray-400">Can you spot the imposter?</p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <div className="card">
            <h2 className="text-2xl font-bold mb-2">Create Room</h2>
            <p className="text-gray-400 mb-6">Host a new game and invite friends</p>
            <div className="space-y-4">
              <input
                className="input"
                placeholder="Your nickname"
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                maxLength={20}
                onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
              />
              <Button className="w-full" size="lg" onClick={handleCreate} loading={loading === 'create'}>
                Create Room
              </Button>
            </div>
          </div>

          <div className="card">
            <h2 className="text-2xl font-bold mb-2">Join Room</h2>
            <p className="text-gray-400 mb-6">Enter a room code to join</p>
            <div className="space-y-4">
              <input
                className="input"
                placeholder="Your nickname"
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                maxLength={20}
              />
              <input
                className="input uppercase tracking-widest text-center font-bold"
                placeholder="ROOM CODE"
                value={joinCode}
                onChange={(e) => setJoinCode(e.target.value.toUpperCase().slice(0, 6))}
                maxLength={6}
                onKeyDown={(e) => e.key === 'Enter' && handleJoin()}
              />
              <Button className="w-full" size="lg" variant="secondary" onClick={handleJoin} loading={loading === 'join'}>
                Join Room
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
