# ZFlow

ZFlow is an AI-powered, one-stop video generation platform.

## High-level architecture

- **Backend (FastAPI)** exposes REST endpoints for task submission, status, and metadata.
- **Worker (async pipeline)** processes prompt-driven generation stages (script → visual → render).
- **Frontend (Vue)** consumes backend APIs and presents the end-user experience.

## Repo navigation

- `backend/` contains the FastAPI application and API surface.
- `worker/` hosts the async generation pipeline and prompt assets.
- `frontend/` contains the Vite + Vue 3 frontend that consumes backend APIs.
- `docs/` captures shared context, architecture, API contracts, and collaboration guidelines.

---

## Quick Start

### One-command setup (macOS/Linux)

```bash
git clone https://github.com/your-username/ZFlow.git
cd ZFlow
./setup.sh
```

The script will:
- Check and install dependencies
- Create Python virtual environment
- Install all Python and Node packages
- Setup environment variables
- Start PostgreSQL
- Create and initialize database

### Start the services

After setup completes, edit `backend/.env` to add your API keys, then start the services:

**Terminal 1 - Backend (port 8000):**
```bash
cd ZFlow
source .venv/bin/activate
cd backend
source .env
uvicorn app.main:app --reload
```

**Terminal 2 - Frontend (port 5173):**
```bash
cd ZFlow/frontend
npm run dev
```

**Open in browser:** http://localhost:5173

**Stop the services:** Press `Ctrl+C` in each terminal.

### Manual setup

### Prerequisites

| Software | Version |
|----------|---------|
| Python | 3.10+ |
| Node.js | 18+ |
| PostgreSQL | 14+ |

### 1. Clone the repository

```bash
git clone https://github.com/your-username/ZFlow.git
cd ZFlow
```

### 2. Install dependencies

**Backend:**
```bash
pip install -r backend/requirements.txt
pip install -r worker/requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
cd ..
```

### 3. Configure environment variables

```bash
cp .env.example backend/.env
```

Edit `backend/.env` and fill in the required values:

```bash
# Database
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/zflow_dev

# LLM Provider (choose one: openai, anthropic, glm)
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key_here
GLM_MODEL=glm-4.7

# Image Provider
IMAGE_PROVIDER=seedream
SEEDREAM_API_KEY=your_api_key_here

# Video Provider
VIDEO_PROVIDER=vidu
VIDU_API_KEY=your_api_key_here
```

**Get API Keys:** https://open.bigmodel.cn/

### 4. Create database

```bash
# Using PostgreSQL CLI
createdb zflow_dev

# Or via psql
psql -U postgres
CREATE DATABASE zflow_dev;
\q
```

### 5. Initialize database tables

```bash
cd backend
python -m app.db.init_db
cd ..
```

### 6. Start services

**Backend (port 8000):**
```bash
cd backend
source .env
uvicorn app.main:app --reload
```

**Frontend (port 5173):**
```bash
cd frontend
npm run dev
```

### 7. Open in browser

Visit http://localhost:5173

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Database connection failed | Check `DATABASE_URL` in `backend/.env` |
| API call failed | Verify API keys are valid |
| Port already in use | Change port in uvicorn/vite command |

---

## Documentation

- `docs/00_PROJECT_CONTEXT.md` - Product intent
- `docs/01_ARCHITECTURE.md` - System architecture
