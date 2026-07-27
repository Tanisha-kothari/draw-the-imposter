# Deployment Guide

## Prerequisites

- [Render](https://render.com) account (backend + database)
- [Vercel](https://vercel.com) account (frontend)
- `git` remote configured

---

## 1. Set up PostgreSQL on Render

1. In Render Dashboard → **New +** → **PostgreSQL**
2. Name: `draw-imposter-db`
3. Region: same as your backend service
4. Plan: **Free** (or paid for production)
5. Copy the **Internal Database URL** once created

---

## 2. Deploy the Backend on Render

### Option A — via `render.yaml` (Blueprint)

Push the repo, then in Render → **Blueprint** → connect repo. Render will auto-detect `render.yaml` and create all resources.

### Option B — Manual (recommended for first time)

1. Render Dashboard → **New +** → **Web Service**
2. Connect your repo
3. Settings:
   - **Name**: `draw-the-imposter-backend`
   - **Environment**: `Python`
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`
4. Add environment variables (under **Advanced**):

| Key             | Value                                                                 |
|-----------------|-----------------------------------------------------------------------|
| `DATABASE_URL`  | `postgresql+asyncpg://user:pass@host:5432/draw_imposter_db` (from step 1) |
| `SECRET_KEY`    | Click **Generate**                                                    |
| `CORS_ORIGINS`  | `["http://localhost:5173","https://draw-the-imp-git-261c37-kotharitanishanilesh-gmailcoms-projects.vercel.app","https://draw-the-imposter-4yyit4g7j.vercel.app","https://draw-the-imposter-as510yw2c.vercel.app"]` |
| `PYTHON_VERSION`| `3.12.0`                                                              |

5. Choose **Free** plan → **Create Web Service**

> **Important**: After first deploy, go to the PostgreSQL service dashboard → **Connections** → copy the **Internal** connection string (not external). Update `DATABASE_URL` accordingly for lower latency.

---

## 3. Deploy the Frontend on Vercel

1. Push your repo to GitHub.
2. Go to [Vercel](https://vercel.com) → **Add New** → **Project**
3. Import your repo → **Root Directory** → select `frontend`
4. **Build & Output Settings**:
   - Framework Preset: **Vite**
   - Build Command: `npm run build`
   - Output Directory: `dist`
5. Environment Variables:

| Key             | Value                                     |
|-----------------|-------------------------------------------|
| `VITE_API_URL`  | `https://draw-the-imposter-backend.onrender.com` |
| `VITE_WS_URL`   | `wss://draw-the-imposter-backend.onrender.com`   |

6. Click **Deploy**

---

## 4. Update CORS for production

The frontend URLs are:
- `https://draw-the-imp-git-261c37-kotharitanishanilesh-gmailcoms-projects.vercel.app`
- `https://draw-the-imposter-4yyit4g7j.vercel.app`
- `https://draw-the-imposter-as510yw2c.vercel.app`

CORS is already configured in `render.yaml` and `config.py` to allow all of these plus `http://localhost:5173`.  
If you need to update it manually on Render:

1. Go to Render → Backend service → **Environment Variables**
2. Update `CORS_ORIGINS` to: `["http://localhost:5173","https://draw-the-imp-git-261c37-kotharitanishanilesh-gmailcoms-projects.vercel.app","https://draw-the-imposter-4yyit4g7j.vercel.app","https://draw-the-imposter-as510yw2c.vercel.app"]`
3. Click **Save Changes** → wait for redeploy

---

## 5. Run database migrations (after backend is live)

Use the Render Shell or a local connection:

```bash
# Local (with DATABASE_URL set to the production PostgreSQL URL)
cd backend
alembic upgrade head

# Or via Render Shell:
#   click on the backend service → Shell → run:
alembic upgrade head
```

---

## 6. Verify deployment

1. Visit `https://draw-the-imposter-backend.onrender.com/health` — should return `{"status":"ok"}`
2. Visit any of the deployed frontend URLs — app should load:
   - `https://draw-the-imp-git-261c37-kotharitanishanilesh-gmailcoms-projects.vercel.app`
   - `https://draw-the-imposter-4yyit4g7j.vercel.app`
   - `https://draw-the-imposter-as510yw2c.vercel.app`
3. Create a room, join, play a round

---

## Troubleshooting

| Problem                         | Likely fix                                                          |
|---------------------------------|----------------------------------------------------------------------|
| Frontend can't connect          | Check `VITE_API_URL` / `VITE_WS_URL` env vars on Vercel             |
| CORS errors in console          | Verify `CORS_ORIGINS` on Render matches the Vercel URL exactly     |
| WebSocket disconnects           | Use `wss://` (not `ws://`) in VITE_WS_URL                           |
| 500 on login / room creation    | Run `alembic upgrade head` against the production DB                |
| SQLite errors in logs           | Set `DATABASE_URL` to the PostgreSQL connection string              |
