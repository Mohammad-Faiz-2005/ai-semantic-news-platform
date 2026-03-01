# Architecture Documentation

## System Architecture
```
┌──────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│              React 18 + Vite + Tailwind CSS                  │
│   Login | Register | Home | Search | Results | Dashboard     │
│         UploadArticle | Profile                              │
└──────────────────────────┬───────────────────────────────────┘
                           │ REST API (JSON)
                           │ Axios + JWT Bearer
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                       FastAPI Backend                        │
│                        Python 3.11                           │
│  /auth  /search  /recommendations  /upload  /analytics       │
└───┬──────────────┬──────────────┬────────────────────────────┘
    │              │              │
    ▼              ▼              ▼
┌────────┐  ┌──────────┐  ┌──────────────┐
│Postgres│  │  FAISS   │  │ SBERT Model  │
│  ORM   │  │IndexFlatIP│  │all-MiniLM-L6 │
│SQLAlch.│  │  .bin    │  │  384-dim     │
└────────┘  └──────────┘  └──────────────┘
```

---

## Semantic Search Request Flow
```
1. User submits query in React SearchBar
2. POST /api/v1/search/semantic { query, top_k }
3. FastAPI auth middleware validates JWT
4. EmbeddingService.embed_text(query)
     └─► SBERTModel.encode_single(text)
         └─► L2-normalised 384-dim float32 vector
5. FAISSService.search(query_embedding, top_k)
     └─► IndexFlatIP.search(query, k)
         └─► Returns [(faiss_idx, score), ...]
         └─► Maps faiss_idx → article_db_id via id_map
6. DB lookup: SELECT * FROM articles WHERE id IN (...)
7. RetrievalService.log_search(user_id, query, top_ids)
8. Return SearchResponse { query, results, retrieval_time_ms }
```

---

## FAISS Index Design

| Property      | Value                                    |
|---------------|------------------------------------------|
| Index type    | `faiss.IndexFlatIP`                      |
| Vector dim    | 384 (all-MiniLM-L6-v2 output)           |
| Normalisation | L2-normalised (inner product = cosine)   |
| Persistence   | `vector_store/faiss_index.bin`           |
| ID mapping    | `vector_store/id_mapping.pkl`            |
| Updates       | Append on article upload, save to disk   |

---

## Recommendation Pipeline
```
GET /api/v1/recommendations
    │
    ├─► Fetch last 50 search queries from search_history
    │
    ├─► EmbeddingService.embed_batch(queries)     → (N, 384)
    │
    ├─► Mean pooling + L2-renormalise             → (384,)
    │
    ├─► FAISSService.search(interest_vec, top_k + seen)
    │
    ├─► Filter already-seen article IDs
    │
    └─► Return top-K ArticleSearchResult[]
         (fallback: latest articles if no history)
```

---

## Database Schema
```sql
-- Users table
CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(120) NOT NULL,
    email           VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role            VARCHAR(20) DEFAULT 'user',
    created_at      TIMESTAMP DEFAULT NOW(),
    is_active       BOOLEAN DEFAULT TRUE
);

-- Articles table
CREATE TABLE articles (
    id                  SERIAL PRIMARY KEY,
    title               VARCHAR(512) NOT NULL,
    content             TEXT NOT NULL,
    domain              VARCHAR(120),
    source              VARCHAR(255),
    created_at          TIMESTAMP DEFAULT NOW(),
    embedding_generated BOOLEAN DEFAULT FALSE
);

-- Search history table
CREATE TABLE search_history (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER REFERENCES users(id) ON DELETE CASCADE,
    query           TEXT NOT NULL,
    top_result_ids  TEXT,          -- JSON-encoded list of article IDs
    timestamp       TIMESTAMP DEFAULT NOW()
);
```

---

## Authentication Flow
```
POST /auth/login { email, password }
    │
    ├─► Verify bcrypt hash
    │
    ├─► create_access_token({ "sub": str(user.id) })
    │       └─► HS256 JWT, expires in 60 min
    │
    └─► Return { access_token, token_type, user }

All protected routes:
    Authorization: Bearer <token>
    │
    └─► get_current_user() dependency
            ├─► decode_access_token(token)
            ├─► DB lookup by user.id
            └─► Return User ORM object
```

---

## Model Comparison

| Model                  | Approach              | Dim    | Accuracy | F1     | Speed     |
|------------------------|-----------------------|--------|----------|--------|-----------|
| TF-IDF + LogReg        | Sparse bag-of-words   | sparse | ~78%     | ~75%   | ~45 ms    |
| BiLSTM                 | Sequential RNN        | 512    | ~84%     | ~82%   | ~38 ms    |
| SBERT (all-MiniLM-L6)  | Transformer embedding | 384    | ~91%     | ~90%   | ~12 ms    |