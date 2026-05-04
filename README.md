# CinemaRec — Hybrid Movie Recommendation System

> Diploma project: hybrid film recommendation system based on user preferences.  
> Stack: FastAPI · Next.js · SQLite · SVD · TF-IDF · TailwindCSS

---

## Setup after cloning

After cloning the repository there are **4 steps** before the app runs.

### Step 1 — Copy environment files

```bash
# Backend
copy backend\.env.example backend\.env          # Windows
# cp backend/.env.example backend/.env          # macOS/Linux

# Frontend
copy frontend\.env.local.example frontend\.env.local     # Windows
# cp frontend/.env.local.example frontend/.env.local     # macOS/Linux
```

> These files are gitignored (local configuration). The defaults work out of the box — no editing needed for local development.

### Step 2 — Backend: install & init DB

```bash
cd backend
python -m venv venv

venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

# Create tables
alembic upgrade head

# Import all movies from CSV + create demo users + generate synthetic ratings
python -m app.utils.seed
```

> `seed` takes 3–5 minutes — it imports 156 000+ movies and generates 800 synthetic users with ratings for collaborative filtering.

### Step 3 — Frontend: install

```bash
cd frontend
npm install
```

### Step 4 — ML training (optional but recommended)

```bash
cd ml
python main.py
```

Trains the TF-IDF content model and SVD collaborative model. Saves to `ml/models/`.  
Without this step the app falls back to popularity-based recommendations.

---

## Running

Open **two terminals**:

```bash
# Terminal 1 — Backend
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

```bash
# Terminal 2 — Frontend
cd frontend
npm run dev
```

| Service | URL |
|---------|-----|
| App | http://localhost:3000 |
| API docs (Swagger) | http://localhost:8000/docs |

---

## Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@cinerarec.com | admin123 |
| User | demo@cinerarec.com | demo123 |

---

## Architecture

```
FinalScore = 0.45 × Collaborative (SVD)
           + 0.40 × Content (TF-IDF cosine similarity)
           + 0.15 × Popularity/Novelty

Cold start (< 5 ratings):
FinalScore = 0.60 × Content + 0.40 × Popularity
```

See [CLAUDE.md](CLAUDE.md) for full architecture documentation.

---

## Project Structure

```
backend/    — FastAPI REST API
frontend/   — Next.js web application  
ml/         — ML training pipeline & evaluation
data_movies_ВКР.csv  — Dataset (156 783 movies)
```

## Requirements

- Python 3.10+
- Node.js 18+
