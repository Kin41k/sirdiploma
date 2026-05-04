# CinemaRec — Hybrid Movie Recommendation System

> Diploma project: hybrid film recommendation system based on user preferences.
> Stack: FastAPI · Next.js · SQLite · SVD · TF-IDF/MiniLM

---

## Quick Start

### 1. Dataset

Place your CSV file at:
```
data/data_movies_ВКР.csv
```

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

# Copy env file
copy .env.example .env

# Init database + import movies from CSV + create demo users
alembic upgrade head
python -m app.utils.seed

# Run dev server
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:3000

### 4. ML Training (optional, improves recommendations)

```bash
cd ml
python main.py
```

Trains SVD and computes content embeddings. Results saved to `ml/models/`.

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
           + 0.40 × Content (TF-IDF cosine)
           + 0.15 × Popularity/Novelty
```

Cold start fallback (< 5 ratings):
```
FinalScore = 0.60 × Content + 0.40 × Popularity
```

See [CLAUDE.md](CLAUDE.md) for full architecture documentation.

---

## Project Structure

```
backend/    — FastAPI REST API
frontend/   — Next.js web application
ml/         — Training pipeline & evaluation
data/       — Dataset CSV
```
