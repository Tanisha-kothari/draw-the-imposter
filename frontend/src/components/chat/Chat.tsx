import { useState } from 'react';
import { useGameStore } from '../../store/gameStore';
import { useWebSocket } from '../../hooks/useWebSocket';

interface ChatProps {
  roomCode?: string;
}

export default function Chat({ roomCode }: ChatProps) {
  const [message, setMessage] = useState('');
  const [isOpen, setIsOpen] = useState(true);
  const messages = useGameStore((s) => s.chatMessages);
  const playerId = useGameStore((s) => s.playerId);

  const { sendMessage } = useWebSocket(roomCode || null, playerId);

  const handleSend = () => {
    if (!message.trim()) return;
    sendMessage('chat_message', { text: message.trim() });
    setMessage('');
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="bg-primary-600 text-white p-3 rounded-full shadow-lg hover:bg-primary-700 transition-colors"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      </button>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl shadow-2xl overflow-hidden">
      <div className="flex items-center justify-between p-3 border-b border-gray-800">
        <h3 className="text-sm font-semibold">Chat</h3>
        <button onClick={() => setIsOpen(false)} className="p-1 hover:bg-gray-800 rounded-lg">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <div className="h-48 overflow-y-auto p-3 space-y-2">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-2 ${msg.player_id === playerId ? 'justify-end' : ''}`}>
            <div className={`max-w-[80%] ${msg.player_id === playerId ? 'bg-primary-600/20' : 'bg-gray-800'} rounded-xl px-3 py-1.5`}>
              <p className="text-xs text-gray-400 font-medium">{msg.nickname}</p>
              <p className="text-sm">{msg.text}</p>
            </div>
          </div>
        ))}
      </div>
      <div className="p-3 border-t border-gray-800 flex gap-2">
        <input
          className="input text-sm flex-1"
          placeholder="Type a message..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          maxLength={200}
        />
        <button onClick={handleSend} className="p-2 bg-primary-600 hover:bg-primary-700 rounded-xl transition-colors">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      </div>
    </div>
  );
}
