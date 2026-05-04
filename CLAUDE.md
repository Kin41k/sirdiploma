# CinemaRec — Hybrid Movie Recommendation System

Diploma project: hybrid film content recommendation system based on user preferences.

## Project Goal

Build a full-stack web application combining Collaborative Filtering, Content-Based Filtering, and Popularity/Novelty ranking into a weighted hybrid recommendation engine.

**Final Score Formula:**
```
FinalScore = 0.45 × Collaborative + 0.40 × Content + 0.15 × PopularityNovelty
```
Cold start fallback (< 5 ratings):
```
FinalScore = 0.60 × Content + 0.40 × PopularityNovelty
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2 |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Database | SQLite (default) — PostgreSQL-ready |
| ML — Content | SentenceTransformers MiniLM (fallback: TF-IDF) |
| ML — Collaborative | Surprise SVD |
| ML — Popularity | Weighted score (vote_average × log(vote_count) × popularity) |
| Frontend | Next.js 14, TypeScript, TailwindCSS |
| State | Zustand |
| Data fetching | TanStack Query (React Query) |

---

## Directory Structure

```
c:\sirdiploma\
├── CLAUDE.md                  ← This file
├── README.md
├── .gitignore
│
├── data/
│   └── data_movies_ВКР.csv    ← Main dataset (place here)
│
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   └── app/
│       ├── main.py            ← FastAPI app entry point
│       ├── config.py          ← Settings (Pydantic BaseSettings)
│       ├── database/
│       │   └── database.py    ← Engine, SessionLocal, Base, get_db
│       ├── models/            ← SQLAlchemy ORM models
│       │   ├── user.py
│       │   ├── movie.py
│       │   ├── rating.py
│       │   └── analytics.py
│       ├── schemas/           ← Pydantic request/response schemas
│       │   ├── user.py
│       │   ├── movie.py
│       │   ├── rating.py
│       │   └── analytics.py
│       ├── auth/
│       │   ├── jwt_handler.py ← Token create/decode, password hash
│       │   └── dependencies.py← get_current_user, get_current_admin
│       ├── api/routes/
│       │   ├── auth.py        ← /api/auth/*
│       │   ├── movies.py      ← /api/movies/*
│       │   ├── recommendations.py ← /api/recommendations/*
│       │   ├── ratings.py     ← /api/ratings/*
│       │   └── admin.py       ← /api/admin/*
│       ├── services/
│       │   ├── user_service.py
│       │   ├── movie_service.py
│       │   └── rating_service.py
│       ├── recommendation/
│       │   ├── hybrid.py      ← HybridRecommender (main engine)
│       │   ├── collaborative.py ← SVD wrapper
│       │   ├── content_based.py ← TF-IDF / MiniLM + cosine
│       │   ├── popularity.py  ← Weighted popularity + novelty
│       │   └── cold_start.py  ← Cold start logic
│       ├── analytics/
│       │   └── tracker.py     ← Click/view tracking, CTR
│       └── utils/
│           └── seed.py        ← DB seed: movies from CSV + demo users
│
├── ml/
│   ├── main.py                ← Run full training pipeline
│   ├── preprocessing/
│   │   ├── load_data.py       ← Load & validate CSV
│   │   └── clean_data.py      ← Genre parsing, text cleanup
│   ├── embeddings/
│   │   └── content_embeddings.py ← Build TF-IDF / MiniLM matrix
│   ├── svd/
│   │   ├── collaborative_model.py ← Surprise SVD wrapper
│   │   └── train_svd.py       ← Train & save SVD model
│   ├── hybrid/
│   │   └── recommender.py     ← Offline hybrid scorer
│   ├── evaluation/
│   │   ├── metrics.py         ← Precision@K, Recall@K, NDCG@K, RMSE
│   │   └── evaluate.py        ← Run evaluation on test split
│   └── models/                ← Saved model artifacts (.pkl, .npy)
│
└── frontend/
    ├── package.json
    ├── tsconfig.json
    ├── tailwind.config.ts
    ├── next.config.ts
    └── src/
        ├── app/
        │   ├── layout.tsx
        │   ├── page.tsx        ← Home: recommendations + popular
        │   ├── globals.css
        │   ├── (auth)/
        │   │   ├── login/page.tsx
        │   │   └── register/page.tsx
        │   ├── movies/[id]/page.tsx
        │   ├── search/page.tsx
        │   ├── onboarding/page.tsx
        │   ├── dashboard/page.tsx
        │   └── admin/page.tsx
        ├── components/
        │   ├── MovieCard.tsx
        │   ├── MovieGrid.tsx
        │   ├── SearchBar.tsx
        │   ├── FilterPanel.tsx
        │   ├── Navbar.tsx
        │   ├── StarRating.tsx
        │   └── SimilarMovies.tsx
        ├── lib/
        │   ├── api.ts          ← Axios instance + all API calls
        │   └── auth.ts         ← Token helpers
        ├── store/
        │   └── authStore.ts    ← Zustand auth state
        ├── hooks/
        │   └── useMovies.ts    ← React Query hooks
        └── types/
            ├── movie.ts
            └── user.ts
```

---

## Database Schema

### users
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| username | VARCHAR UNIQUE | |
| email | VARCHAR UNIQUE | |
| password_hash | VARCHAR | bcrypt |
| role | ENUM | user / admin |
| created_at | DATETIME | UTC |

### movies
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | from CSV |
| title | VARCHAR | indexed |
| vote_average | FLOAT | |
| vote_count | INTEGER | |
| runtime | INTEGER | minutes |
| original_language | VARCHAR | |
| overview | TEXT | |
| popularity | FLOAT | |
| genres | VARCHAR | JSON array string |
| keywords | VARCHAR | JSON array string |
| year | INTEGER | |
| poster_url | VARCHAR | TMDB URL |
| country | VARCHAR | |

### ratings
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| user_id | FK → users | |
| movie_id | FK → movies | |
| rating | FLOAT | 0.5–5.0 |
| timestamp | DATETIME | UTC |

### movie_clicks
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| movie_id | FK → movies UNIQUE | |
| clicks | INTEGER | |
| views | INTEGER | |

### recommendation_clicks
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| user_id | FK → users | |
| movie_id | FK → movies | |
| source | VARCHAR | recommendation / search / similar |
| timestamp | DATETIME | UTC |

---

## API Endpoints

```
POST   /api/auth/register        — Register new user
POST   /api/auth/login           — Login, get JWT
GET    /api/auth/me              — Current user info

GET    /api/movies/              — List/search/filter movies
GET    /api/movies/{id}          — Movie detail + similar movies

GET    /api/recommendations/     — Personal recommendations (JWT required)
GET    /api/recommendations/popular — Popular movies (no auth)
GET    /api/recommendations/similar/{movie_id} — Similar movies

POST   /api/ratings/             — Rate a movie (JWT required)
GET    /api/ratings/my           — User's ratings

GET    /api/admin/stats          — Overall stats (admin)
GET    /api/admin/analytics      — Genre/country/year analytics
GET    /api/admin/metrics        — Precision@K, NDCG@K etc.
GET    /api/admin/users          — User list
```

---

## ML Pipeline

### Training (run once or periodically):
```bash
cd ml
python main.py
```
Steps:
1. Load `data/data_movies_ВКР.csv`
2. Clean genres/keywords (parse JSON strings)
3. Build combined text field: `title + genres + keywords + overview + language + year`
4. Compute TF-IDF matrix → save `ml/models/tfidf_matrix.npz` + `ml/models/tfidf_vectorizer.pkl`
5. (Optional) Compute MiniLM embeddings → save `ml/models/embeddings.npy`
6. Load DB ratings → train Surprise SVD → save `ml/models/svd_model.pkl`
7. Compute Precision@10, Recall@10, NDCG@10, RMSE → print report

### Hybrid Scoring:
```python
# Cold start (< 5 ratings)
score = 0.60 * content_score + 0.40 * popularity_score

# Normal user
score = 0.45 * cf_score + 0.40 * content_score + 0.15 * popularity_score
```

### Popularity score:
```python
import numpy as np
score = (vote_average / 10) * np.log1p(vote_count) * np.tanh(popularity / 500)
```

---

## Setup & Run

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Init DB + seed data
alembic upgrade head
python -m app.utils.seed

# Run
uvicorn app.main:app --reload --port 8000
# Swagger: http://localhost:8000/docs
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# http://localhost:3000
```

### ML Training
```bash
cd ml
python main.py
```

---

## Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@cinerarec.com | admin123 |
| User | demo@cinerarec.com | demo123 |

---

## Evaluation Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| Precision@K | TP / K | > 0.15 |
| Recall@K | TP / relevant | > 0.10 |
| NDCG@K | DCG / IDCG | > 0.20 |
| RMSE | √(Σ(pred−actual)²/n) | < 0.90 |

---

## Key Design Decisions

- **No Docker**: simple local SQLite setup for academic demo
- **PostgreSQL-ready**: `DATABASE_URL` env var, no sqlite-specific code in ORM
- **SVD cold start**: if user has < 5 ratings, skip CF entirely
- **TF-IDF default**: lighter than MiniLM, works without GPU. MiniLM optional via env flag
- **Lazy model loading**: recommendation engine loads models at first request, not at import time
- **Seed script**: imports movies from CSV into SQLite so backend has data immediately
