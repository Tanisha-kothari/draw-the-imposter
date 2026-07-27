# Draw the Imposter

A turn-based online multiplayer drawing game built with FastAPI + React + WebSockets.

## Overview

One player is secretly the Imposter. Everyone else knows the drawing prompt. Players take turns adding to the same shared drawing. After everyone has drawn, players vote on who they believe the imposter is. The imposter wins by blending into the drawing without ever knowing the secret word.

## Tech Stack

| Layer   | Technology                                      |
| ------- | ----------------------------------------------- |
| Frontend | React, Vite, TypeScript, Tailwind CSS, Zustand  |
| Backend  | FastAPI (Python 3.12+), WebSockets, SQLAlchemy, Alembic |
| Database | SQLite (dev) / PostgreSQL + Supabase (production) |
| Deployment | Frontend → Vercel, Backend → Render, DB → Supabase |

## Project Structure

```
draw-the-imposter/
├── backend/
│   ├── app/
│   │   ├── config.py          # Settings & env vars
│   │   ├── main.py            # FastAPI app entry point
│   │   ├── database/          # SQLAlchemy async engine & session
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── repositories/      # Data access layer (CRUD)
│   │   ├── services/          # Business logic layer
│   │   ├── routers/           # REST API routes
│   │   ├── websocket/         # WebSocket manager & message handler
│   │   └── utils/             # Game state machine, word bank
│   ├── alembic/               # Database migrations
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/             # Home, Room, Game
│   │   ├── components/        # UI components (canvas, chat, etc.)
│   │   ├── store/             # Zustand state stores
│   │   ├── hooks/             # useWebSocket hook
│   │   ├── lib/               # API client, canvas helpers, constants
│   │   └── types/             # TypeScript type definitions
│   ├── package.json
│   └── .env.example
├── docker-compose.yml
├── render.yaml
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.12+ (tested with 3.12, 3.13, 3.14)
- Node.js 18+
- npm 9+

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (recommended)
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env if needed (defaults work for local dev with SQLite)

# Apply database migrations
alembic upgrade head

# Start the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Health check: `http://localhost:8000/health`

### Frontend Setup

```bash
# Navigate to frontend directory (from project root)
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Defaults point to local backend at localhost:8000

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`.

### Docker (Alternative)

```bash
# Start all services
docker-compose up -d

# Backend: http://localhost:8000
# Frontend: http://localhost:80
```

## Environment Variables

### Backend (`backend/.env`)

| Variable       | Description                          | Default                                      |
| -------------- | ------------------------------------ | -------------------------------------------- |
| `DATABASE_URL` | Database connection string            | `sqlite+aiosqlite:///./draw_imposter.db`      |
| `SECRET_KEY`   | Secret key for session/auth           | `dev-secret-key-change-in-production`         |
| `CORS_ORIGINS` | Allowed CORS origins (JSON array)     | `["http://localhost:5173"]`                   |
| `SUPABASE_URL` | Supabase project URL (production)     | _(optional)_                                  |
| `SUPABASE_KEY` | Supabase service key (production)     | _(optional)_                                  |

### Frontend (`frontend/.env`)

| Variable       | Description                | Default                     |
| -------------- | -------------------------- | --------------------------- |
| `VITE_API_URL` | Backend API URL            | `http://localhost:8000`     |
| `VITE_WS_URL`  | Backend WebSocket URL      | `ws://localhost:8000`       |

## Database

### Local Development (SQLite)

SQLite is used by default for zero-config development. The database file (`draw_imposter.db`) is created automatically in the `backend/` directory.

### Production (Supabase PostgreSQL)

1. Create a free Supabase project at [supabase.com](https://supabase.com)
2. Go to Project Settings → Database → Connection string
3. Copy the connection string (use the URI format with `asyncpg`)
4. Set `DATABASE_URL` in your backend environment:

```
DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@[HOST]:5432/postgres
```

### Migrations

```bash
cd backend

# Create a new migration after model changes
alembic revision --autogenerate -m "description_of_changes"

# Apply pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## Game Flow

1. **Lobby** - Create or join a room with a 6-character code
2. **Settings** - Host configures rounds, timers, difficulty, etc.
3. **Role Assignment** - Server randomly assigns one Imposter
4. **Drawing** - Each player draws in turn (configurable timer)
5. **Reveal** - All drawings are shown without player attribution
6. **Voting** - Players vote for the suspected imposter
7. **Results** - Winner revealed, scores updated, per-player strokes shown
8. **Next Round** - New word, new imposter, canvas cleared
9. **Game Over** - Final leaderboard and option to play again

## WebSocket Messages

### Client → Server

| Type              | Data                          | Description                        |
| ----------------- | ----------------------------- | ---------------------------------- |
| `join_room`       | —                             | Reconnect to room                  |
| `leave_room`      | —                             | Leave the room                     |
| `ready`           | `{ is_ready: bool }`          | Toggle ready status                |
| `start_game`      | —                             | (Host only) Start the game         |
| `drawing_update`  | `{ stroke_data }`             | Real-time stroke broadcast         |
| `drawing_submit`  | `{ image_data, stroke_data }` | Submit completed drawing           |
| `vote_submit`     | `{ target_player_id }`        | Cast a vote                        |
| `chat_message`    | `{ text }`                    | Send a chat message                |
| `update_settings` | `{ max_players, ... }`        | (Host only) Update room settings   |
| `kick_player`     | `{ player_id }`               | (Host only) Kick a player          |
| `play_again`      | —                             | Reset game for a new session       |

### Server → Client

| Type               | Data                                   | Description                           |
| ------------------ | -------------------------------------- | ------------------------------------- |
| `phase_change`     | `{ phase }`                            | Game phase changed                    |
| `players_list`     | `{ players: [...] }`                   | Full player list update               |
| `player_joined`    | `{ player_id, nickname }`              | A player joined                       |
| `player_left`      | `{ player_id, nickname }`              | A player left                         |
| `player_ready`     | `{ player_id, is_ready }`              | Player ready status changed           |
| `word_assigned`    | `{ word_hint, is_imposter, role }`     | Secret word / imposter assignment     |
| `turn_change`      | `{ current_player_id, turn_number }`   | Drawing turn changed                  |
| `timer_sync`       | `{ phase, time_remaining }`            | Countdown timer sync                  |
| `timer_end`        | `{ phase }`                            | Timer expired                         |
| `drawing_broadcast`| `{ stroke_data, player_id }`           | Real-time stroke from active drawer   |
| `drawing_confirmed`| `{ success }`                          | Drawing submission confirmed          |
| `reveal_drawings`  | `{ drawings: [...] }`                  | Reveal all round drawings             |
| `vote_confirmed`   | `{ success }`                          | Vote recorded                         |
| `round_results`    | `{ results, game_result, round }`      | Round results + scores                |
| `round_start`      | `{ round, total_rounds }`              | Next round started                    |
| `chat_message`     | `{ player_id, nickname, text }`        | Chat message from another player      |
| `settings_updated` | `{ ...settings }`                      | Room settings updated                 |
| `error`            | `{ message }`                          | Error notification                    |
| `kick`             | `{ message }`                          | You were kicked from the room         |

## Deployment

### Frontend → Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Navigate to frontend
cd frontend

# Deploy
vercel --prod

# Set environment variables in Vercel dashboard:
# VITE_API_URL=https://your-backend.onrender.com
# VITE_WS_URL=wss://your-backend.onrender.com
```

### Backend → Render

1. Push the repository to GitHub
2. Create a new **Web Service** on [Render](https://render.com)
3. Connect your GitHub repository
4. Configure:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Set environment variables:
   - `DATABASE_URL`: Your Supabase PostgreSQL connection string
   - `SECRET_KEY`: Generate a secure random key
   - `CORS_ORIGINS`: `["https://your-frontend.vercel.app"]`
6. Deploy

### Database → Supabase (Free Tier)

1. Create a free Supabase project
2. Go to Project Settings → Database → Connection string
3. Use the URI connection string with `asyncpg` driver:
   ```
   postgresql+asyncpg://postgres:[PASSWORD]@[HOST]:5432/postgres
   ```
4. Run migrations:
   ```bash
   cd backend
   DATABASE_URL="postgresql+asyncpg://..." alembic upgrade head
   ```

### Using `render.yaml` (Blueprint)

The project includes `render.yaml` for Infrastructure-as-Code deployment on Render. Connect your repository and Render will automatically create the backend, frontend (static site), and database services.

## Features

- **Server-authoritative game logic** - All validation on the server, never trust the client
- **Individual word assignment** - Imposters never see the secret word
- **Turn management** - Only the active player can draw
- **Real-time stroke broadcasting** - Other players see drawing progress live
- **Configurable game settings** - Rounds, timers, difficulty, categories
- **Touch and mouse support** - Responsive canvas for all devices
- **High-DPI support** - Crisp rendering on Retina displays
- **Auto-reconnection** - Automatically reconnects on connection loss
- **Chat system** - Communicate between rounds
- **Humble word bank** - 5 categories × 3 difficulty levels
- **Host controls** - Kick players, update settings
- **Circular countdown timers** - Visual timer for drawing and voting phases

## Anti-Cheat Measures

- Server decides roles, words, and turn order
- Drawing phase is enforced server-side
- Voting is one-time and immutable
- Timer durations are validated on the server
- Client-side code never contains the secret word
- All stroke submissions are validated before storage

## License

MIT
