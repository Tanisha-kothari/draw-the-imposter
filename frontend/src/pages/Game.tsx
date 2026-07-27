import { useCallback, useMemo, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useGameStore } from '../store/gameStore';
import { useWebSocket } from '../hooks/useWebSocket';
import DrawingCanvas, { DrawingCanvasHandle } from '../components/canvas/DrawingCanvas';
import CanvasViewer from '../components/canvas/CanvasViewer';
import CountdownTimer from '../components/ui/CountdownTimer';
import Button from '../components/ui/Button';
import Avatar from '../components/ui/Avatar';
import Chat from '../components/chat/Chat';

export default function Game() {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();
  const playerId = useGameStore((s) => s.playerId);
  const { sendMessage } = useWebSocket(code || null, playerId);

  const phase = useGameStore((s) => s.phase);
  const currentRound = useGameStore((s) => s.currentRound);
  const totalRounds = useGameStore((s) => s.totalRounds);
  const wordHint = useGameStore((s) => s.wordHint);
  const wordCategory = useGameStore((s) => s.wordCategory);
  const timeRemaining = useGameStore((s) => s.timeRemaining);
  const isImposter = useGameStore((s) => s.isImposter);
  const hasVoted = useGameStore((s) => s.hasVoted);
  const drawingSubmitted = useGameStore((s) => s.drawingSubmitted);
  const players = useGameStore((s) => s.players);
  const revealDrawings = useGameStore((s) => s.revealDrawings);
  const gameResult = useGameStore((s) => s.gameResult);
  const settings = useGameStore((s) => s.settings);
  const currentTurnPlayerId = useGameStore((s) => s.currentTurnPlayerId);
  const isHost = useGameStore((s) => s.isHost);
  const roundStrokes = useGameStore((s) => s.roundStrokes);
  const awaitingNextRound = useGameStore((s) => s.awaitingNextRound);
  const setDrawingSubmitted = useGameStore((s) => s.setDrawingSubmitted);

  const canvasRef = useRef<DrawingCanvasHandle>(null);
  const prevRoundStrokesRef = useRef<string>('');

  // Load shared canvas strokes into DrawingCanvas when they change
  useEffect(() => {
    const key = JSON.stringify(roundStrokes);
    if (key !== prevRoundStrokesRef.current) {
      prevRoundStrokesRef.current = key;
      canvasRef.current?.loadStrokes(roundStrokes);
    }
  }, [roundStrokes]);

  const isMyTurn = currentTurnPlayerId === playerId;
  const canDraw = phase === 'drawing' && isMyTurn && !drawingSubmitted;

  const handleSubmitDrawing = useCallback(() => {
    const imageData = canvasRef.current?.getImageData() || '';
    const strokes = canvasRef.current?.getStrokes() || [];
    sendMessage('drawing_submit', {
      image_data: imageData,
      stroke_data: strokes.length > 0 ? strokes : null,
    });
    setDrawingSubmitted(true);
  }, [sendMessage, setDrawingSubmitted]);

  const handleVote = useCallback((targetId: string) => {
    sendMessage('vote_submit', { target_player_id: targetId });
  }, [sendMessage]);

  const handleNextRound = useCallback(() => {
    sendMessage('next_round', {});
  }, [sendMessage]);

  const handlePlayAgain = useCallback(() => {
    sendMessage('play_again', {});
  }, [sendMessage]);

  const handleLeave = useCallback(() => {
    navigate('/');
  }, [navigate]);

  const handleTimerEnd = useCallback(() => {
    if (phase === 'drawing' && !drawingSubmitted && isMyTurn) {
      handleSubmitDrawing();
    }
  }, [phase, drawingSubmitted, isMyTurn, handleSubmitDrawing]);

  const currentPlayer = useMemo(() =>
    players.find(p => p.id === currentTurnPlayerId),
    [players, currentTurnPlayerId]
  );

  if (!code || !playerId) {
    navigate('/');
    return null;
  }

  return (
    <div className="min-h-screen p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-400">Room: <span className="font-mono text-primary-400">{code}</span></span>
            {(phase === 'drawing' || phase === 'reveal' || phase === 'voting' || phase === 'results') && (
              <span className="text-sm font-medium bg-gray-800 px-3 py-1 rounded-full">
                Round {currentRound}/{totalRounds || settings?.num_rounds || 3}
              </span>
            )}
          </div>
          <div className="flex items-center gap-3">
            {timeRemaining > 0 && (phase === 'drawing' || phase === 'voting') && (
              <CountdownTimer
                timeRemaining={timeRemaining}
                totalTime={phase === 'drawing' ? (settings?.drawing_time || 60) : (settings?.voting_time || 30)}
                onComplete={handleTimerEnd}
                size="sm"
              />
            )}
          </div>
        </div>

        <div className="grid lg:grid-cols-4 gap-6">
          <div className="lg:col-span-1">
            <div className="card">
              <h3 className="text-sm font-semibold text-gray-400 mb-3">Players</h3>
              <div className="space-y-2">
                {players.map((p, i) => (
                  <div
                    key={p.id}
                    className={`flex items-center gap-2 p-2 rounded-lg transition-colors ${
                      phase === 'drawing' && p.id === currentTurnPlayerId
                        ? 'bg-primary-600/20 ring-1 ring-primary-500'
                        : 'bg-gray-800/50'
                    }`}
                  >
                    <Avatar nickname={p.nickname} colorIndex={i} size="sm" />
                    <span className="text-sm truncate flex-1">
                      {p.nickname}
                      {p.id === playerId && <span className="text-gray-500"> (you)</span>}
                      {phase === 'drawing' && p.id === currentTurnPlayerId && (
                        <span className="text-primary-400 text-xs ml-1">drawing...</span>
                      )}
                    </span>
                    {phase === 'voting' && p.id !== playerId && !hasVoted && (
                      <button
                        onClick={() => handleVote(p.id)}
                        className="text-xs bg-primary-600 hover:bg-primary-700 px-2 py-1 rounded-lg transition-colors shrink-0"
                      >
                        Vote
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {(phase === 'results' || phase === 'game_over') && awaitingNextRound && (
              <div className="mt-4 card text-center py-4">
                <p className="text-gray-400 text-sm">
                  Waiting for host to continue...
                </p>
              </div>
            )}
          </div>

          <div className="lg:col-span-3">
            {phase === 'assign_roles' && (
              <div className="card flex flex-col items-center justify-center py-20">
                <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mb-4" />
                <h2 className="text-2xl font-bold text-primary-400">Assigning Roles...</h2>
                <p className="text-gray-400 mt-2">The imposter is being chosen</p>
              </div>
            )}

            {phase === 'drawing' && (
              <div className="space-y-4">
                <div className="card">
                  {isImposter ? (
                    <div className="text-center">
                      <h2 className="text-2xl font-bold text-red-400">You are the Imposter!</h2>
                      <p className="text-gray-400 mt-1">Try to blend in and guess the word</p>
                      {wordCategory && (
                        <div className="mt-3 inline-block bg-gray-800 px-4 py-2 rounded-lg">
                          <p className="text-xs text-gray-500">Category</p>
                          <p className="text-lg font-bold text-yellow-400">{wordCategory}</p>
                          <p className="text-sm text-gray-400 mt-1">Word: ???</p>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center">
                      <h2 className="text-sm text-gray-400 mb-1">Draw this word:</h2>
                      {wordCategory && (
                        <p className="text-sm text-yellow-400 font-medium mb-1">Category: {wordCategory}</p>
                      )}
                      <p className="text-3xl font-bold text-primary-400 tracking-wide">{wordHint}</p>
                    </div>
                  )}
                  <div className="mt-3 text-center">
                    {currentPlayer && (
                      <p className="text-sm text-gray-500">
                        {isMyTurn ? 'Your turn to draw!' : `${currentPlayer.nickname} is drawing...`}
                      </p>
                    )}
                  </div>
                </div>

                <DrawingCanvas
                  ref={canvasRef}
                  readOnly={!canDraw}
                  width={600}
                  height={400}
                />

                <div className="flex justify-center gap-3">
                  {canDraw ? (
                    <Button size="lg" onClick={handleSubmitDrawing}>
                      Submit Drawing
                    </Button>
                  ) : drawingSubmitted ? (
                    <p className="text-green-400 font-medium flex items-center justify-center gap-2">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      Drawing submitted!
                    </p>
                  ) : (
                    <p className="text-gray-500">Waiting for your turn...</p>
                  )}
                </div>
              </div>
            )}

            {phase === 'reveal' && (
              <div className="space-y-4">
                <div className="text-center">
                  <h2 className="text-2xl font-bold">Reveal Phase</h2>
                  <p className="text-gray-400 mt-1">Study the drawing before voting</p>
                </div>
                <div className="card flex justify-center">
                  <CanvasViewer
                    combinedStrokes={roundStrokes}
                    width={500}
                    height={350}
                  />
                </div>
                <div className="text-center text-sm text-gray-500 animate-pulse">
                  Voting starts soon...
                </div>
              </div>
            )}

            {phase === 'voting' && (
              <div className="space-y-4">
                <div className="text-center">
                  <h2 className="text-2xl font-bold">Vote for the Imposter!</h2>
                  <p className="text-gray-400 mt-1">Choose who you think is the imposter</p>
                </div>

                <div className="card flex justify-center">
                  <CanvasViewer
                    combinedStrokes={roundStrokes}
                    width={500}
                    height={350}
                  />
                </div>

                <div className="card">
                  <h3 className="text-lg font-semibold mb-3">Cast your vote</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {players
                      .filter((p) => p.id !== playerId)
                      .map((p) => (
                        <Button
                          key={p.id}
                          onClick={() => handleVote(p.id)}
                          disabled={hasVoted}
                          variant={hasVoted ? 'secondary' : 'primary'}
                        >
                          {p.nickname}
                        </Button>
                      ))}
                  </div>
                  {hasVoted && (
                    <p className="text-green-400 text-center font-medium flex items-center justify-center gap-2 mt-3">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      Vote submitted! Waiting for others...
                    </p>
                  )}
                </div>
              </div>
            )}

            {phase === 'results' && (
              <div className="space-y-6">
                <div className="card text-center">
                  <h2 className={`text-3xl font-bold mb-2 ${gameResult?.winner === 'imposter' ? 'text-red-400' : 'text-green-400'}`}>
                    {gameResult?.winner === 'imposter' ? 'Imposter Wins!' : 'Innocents Win!'}
                  </h2>
                  <p className={`text-lg font-semibold ${gameResult?.winner === 'imposter' ? 'text-red-400' : 'text-green-400'}`}>
                    {gameResult?.winner === 'imposter' ? '✘ Imposter Escaped' : '✔ Imposter Caught'}
                  </p>

                  <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                    {gameResult?.category && (
                      <div className="bg-gray-800/50 rounded-lg p-3">
                        <p className="text-xs text-gray-500">Category</p>
                        <p className="text-lg font-bold text-yellow-400">{gameResult.category}</p>
                      </div>
                    )}
                    {gameResult?.word && (
                      <div className="bg-gray-800/50 rounded-lg p-3">
                        <p className="text-xs text-gray-500">Secret Word</p>
                        <p className="text-lg font-bold text-primary-400">{gameResult.word}</p>
                      </div>
                    )}
                    <div className="bg-gray-800/50 rounded-lg p-3">
                      <p className="text-xs text-gray-500">Actual Imposter</p>
                      <p className="text-lg font-bold text-red-400">{gameResult?.imposter_nickname}</p>
                    </div>
                  </div>

                  <div className="mt-4 flex justify-center">
                    <CanvasViewer
                      combinedStrokes={roundStrokes}
                      width={400}
                      height={280}
                    />
                  </div>
                </div>

                {gameResult?.vote_details && gameResult.vote_details.length > 0 && (
                  <div className="card">
                    <h3 className="text-lg font-semibold mb-3">Votes</h3>
                    <div className="space-y-2">
                      {gameResult.vote_details.map((v, i) => (
                        <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-gray-800/50">
                          <span>{v.voter_nickname}</span>
                          <span className="text-gray-400 mx-2">→</span>
                          <span className="font-medium">{v.target_nickname}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="card">
                  <h3 className="text-lg font-semibold mb-3">Scoreboard</h3>
                  <div className="space-y-2">
                    {(gameResult?.scores || [])
                      .slice()
                      .sort((a: any, b: any) => b.score - a.score)
                      .map((s: any, i: number) => (
                        <div key={s.player_id} className="flex items-center justify-between p-2 rounded-lg bg-gray-800/50">
                          <div className="flex items-center gap-2">
                            <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${i === 0 ? 'bg-yellow-500 text-black' : 'bg-gray-700'}`}>
                              {i + 1}
                            </span>
                            <span>{s.nickname}</span>
                            {s.player_id === gameResult?.imposter_id && (
                              <span className="text-xs bg-red-600/20 text-red-400 px-2 py-0.5 rounded-full">Imposter</span>
                            )}
                          </div>
                          <span className="font-bold text-primary-400">{s.score}</span>
                        </div>
                      ))}
                  </div>
                </div>

                <div className="flex justify-center gap-3">
                  {isHost ? (
                    <Button size="lg" onClick={handleNextRound} disabled={!awaitingNextRound}>
                      Next Round
                    </Button>
                  ) : (
                    <p className="text-gray-400 text-center">Waiting for host to continue...</p>
                  )}
                  <Button variant="secondary" onClick={handleLeave}>Leave Game</Button>
                </div>
              </div>
            )}

            {phase === 'game_over' && (
              <div className="space-y-6">
                <div className="card text-center">
                  <h2 className={`text-3xl font-bold mb-2 ${gameResult?.winner === 'imposter' ? 'text-red-400' : 'text-green-400'}`}>
                    {gameResult?.winner === 'imposter' ? 'Imposter Wins!' : 'Innocents Win!'}
                  </h2>
                  <p className={`text-lg font-semibold ${gameResult?.winner === 'imposter' ? 'text-red-400' : 'text-green-400'}`}>
                    {gameResult?.winner === 'imposter' ? '✘ Imposter Escaped' : '✔ Imposter Caught'}
                  </p>
                  <p className="text-gray-400">
                    The imposter was <span className="font-bold text-white">{gameResult?.imposter_nickname}</span>
                  </p>

                  <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                    {gameResult?.category && (
                      <div className="bg-gray-800/50 rounded-lg p-3">
                        <p className="text-xs text-gray-500">Category</p>
                        <p className="text-lg font-bold text-yellow-400">{gameResult.category}</p>
                      </div>
                    )}
                    {gameResult?.word && (
                      <div className="bg-gray-800/50 rounded-lg p-3">
                        <p className="text-xs text-gray-500">Secret Word</p>
                        <p className="text-lg font-bold text-primary-400">{gameResult.word}</p>
                      </div>
                    )}
                    <div className="bg-gray-800/50 rounded-lg p-3">
                      <p className="text-xs text-gray-500">Actual Imposter</p>
                      <p className="text-lg font-bold text-red-400">{gameResult?.imposter_nickname}</p>
                    </div>
                  </div>
                </div>

                <div className="card">
                  <h3 className="text-lg font-semibold mb-3">Scoreboard</h3>
                  <div className="space-y-2">
                    {(gameResult?.scores || [])
                      .slice()
                      .sort((a: any, b: any) => b.score - a.score)
                      .map((s: any, i: number) => (
                        <div key={s.player_id} className="flex items-center justify-between p-2 rounded-lg bg-gray-800/50">
                          <div className="flex items-center gap-2">
                            <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${i === 0 ? 'bg-yellow-500 text-black' : 'bg-gray-700'}`}>
                              {i + 1}
                            </span>
                            <span>{s.nickname}</span>
                            {s.player_id === gameResult?.imposter_id && (
                              <span className="text-xs bg-red-600/20 text-red-400 px-2 py-0.5 rounded-full">Imposter</span>
                            )}
                          </div>
                          <span className="font-bold text-primary-400">{s.score}</span>
                        </div>
                      ))}
                  </div>
                </div>

                <div className="flex justify-center gap-3">
                  <Button onClick={handlePlayAgain}>Play Again</Button>
                  <Button variant="secondary" onClick={handleLeave}>Leave Game</Button>
                </div>
              </div>
            )}

            {phase === 'lobby' && (
              <div className="card text-center py-20">
                <h2 className="text-2xl font-bold mb-2">Returning to Lobby...</h2>
                <p className="text-gray-400">Game has ended or been cancelled</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
