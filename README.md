# AI-Powered Semantic News Retrieval and Recommendation Platform

A production-ready full-stack web application that performs **semantic search**
and **personalised recommendations** for news articles using Sentence-BERT
embeddings and FAISS vector indexing.

---

## Tech Stack

| Layer        | Technology                                   |
|--------------|----------------------------------------------|
| Frontend     | React 18, Vite, Tailwind CSS, Chart.js       |
| Backend      | FastAPI, Python 3.11, SQLAlchemy 2.0         |
| Database     | PostgreSQL 15                                |
| Vector Store | FAISS IndexFlatIP                            |
| ML Models    | Sentence-BERT (all-MiniLM-L6-v2), LSTM, TF-IDF |
| Auth         | JWT (python-jose) + bcrypt                   |
| Deployment   | Docker + Docker Compose                      |

---

## Quick Start

### Prerequisites
- Docker ≥ 24
- Docker Compose ≥ 2

### Step 1 — Configure environment
```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### Step 2 — Build and launch all services
```bash
docker-compose up --build
```

This starts:
- **PostgreSQL** on port `5432`
- **FastAPI backend** on port `8000`
- **React frontend** on port `5173`

### Step 3 — Seed the database

Open a second terminal after services are healthy:
```bash
docker-compose exec backend python -m app.seed.seed_data
```

This creates:
- Admin: `admin@newsplatform.com` / `Admin@1234`
- User: `user@newsplatform.com` / `User@1234`
- 12 sample articles with FAISS embeddings

### Step 4 — Open the app

Navigate to **http://localhost:5173**

---

## Local Development (without Docker)

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Set DATABASE_URL to local Postgres
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env            # Set VITE_API_BASE_URL
npm run dev
```

---

## API Reference

| Method | Endpoint                              | Description                  | Auth       |
|--------|---------------------------------------|------------------------------|------------|
| POST   | `/api/v1/auth/register`               | Register new user            | Public     |
| POST   | `/api/v1/auth/login`                  | Login → JWT token            | Public     |
| GET    | `/api/v1/auth/me`                     | Get current user profile     | JWT        |
| POST   | `/api/v1/search/semantic`             | SBERT + FAISS search         | JWT        |
| POST   | `/api/v1/search/tfidf`                | TF-IDF baseline search       | JWT        |
| GET    | `/api/v1/recommendations`             | Personalised recommendations | JWT        |
| POST   | `/api/v1/upload`                      | Upload & index article       | Admin JWT  |
| GET    | `/api/v1/upload/articles`             | List all articles            | Admin JWT  |
| GET    | `/api/v1/analytics`                   | Stats + model metrics        | JWT        |
| GET    | `/api/v1/analytics/loss-curves`       | LSTM training curves         | JWT        |
| GET    | `/api/v1/analytics/retrieval-comparison` | Speed comparison          | JWT        |

**Interactive Swagger docs:** http://localhost:8000/docs

---

## ML Pipeline
```bash
cd ml_pipeline
pip install -r requirements.txt

# Evaluate SBERT on 20 Newsgroups
python train_sbert.py

# Train BiLSTM classifier
python train_lstm.py

# Full model comparison with confusion matrices
python evaluate_models.py

# Rebuild FAISS index from live database
python generate_embeddings.py --db-url postgresql://newsuser:newspassword@localhost:5432/newsdb
```

---

## Project Structure
```
ai-semantic-news-platform/
├── backend/
│   └── app/
│       ├── api/           # FastAPI routers (auth, search, recommendation, upload, analytics)
│       ├── models/        # ML model wrappers (SBERT, LSTM, Hybrid)
│       ├── services/      # Business logic (embedding, FAISS, retrieval, recommendation)
│       ├── database/      # ORM models, schemas, DB session
│       ├── utils/         # Security, preprocessing, evaluation helpers
│       ├── seed/          # Sample data seeder
│       └── core/          # Logging config, constants
├── frontend/
│   └── src/
│       ├── pages/         # 8 React pages
│       ├── components/    # Navbar, SearchBar, ResultCard, RecommendationCard
│       ├── context/       # AuthContext (JWT state)
│       ├── routes/        # ProtectedRoute
│       └── api/           # Axios instance
├── ml_pipeline/           # Offline training & evaluation scripts + notebooks
├── vector_store/          # FAISS index (auto-generated on seed)
└── docker-compose.yml
```