# GISUL — Get Intelligence from Similar User Learning

> A Flask web app that uses AI embeddings to find semantically similar study questions from your personal history, powered by Qdrant Cloud vector search.

---

## Project Structure

```
gisul/
├── .env                      ← All credentials (never commit this)
├── .gitignore
├── README.md
├── requirements.txt
├── run.py                    ← Entry point: python run.py
│
├── app.py                    ← Flask app: routes, SQLite models, auth
├── embedding_model.py        ← AI: sentence embeddings + topic tagger
├── qdrant_store.py           ← Qdrant Cloud: store & search vectors
│
├── templates/
│   ├── base.html             ← Shared dark theme layout + nav
│   ├── login.html            ← Login form
│   ├── register.html         ← Registration form
│   ├── dashboard.html        ← Ask a question + see similar results
│   └── history.html          ← Browse all past questions by topic
│
├── static/
│   └── style.css             ← Shared stylesheet
│
└── tests/
    └── test_questions.py     ← Integration tests + Excel export
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web Framework | Flask + Flask-Login + Flask-SQLAlchemy |
| Embedding Model | `all-MiniLM-L6-v2` (sentence-transformers) |
| Vector Database | Qdrant Cloud (384-dim, Cosine similarity) |
| Relational DB | SQLite (users, questions, history) |
| Auth | Werkzeug PBKDF2-SHA256 password hashing |
| Testing | Python unittest + openpyxl (Excel report) |

---

## Setup

### 1. Clone & create virtual environment

```bash
git clone <repo-url>
cd gisul
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
copy .env.example .env
```

```env
SECRET_KEY=your-flask-secret-key
DATABASE_URL=sqlite:///database.db
QDRANT_URL=https://<your-cluster>.qdrant.io:6333
QDRANT_API_KEY=<your-api-key>
QDRANT_COLLECTION=gisul_questions
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### 4. Run the app

```bash
python run.py
```

Visit `http://127.0.0.1:5000`

---

## How It Works

```
User submits a question
        │
        ▼
  get_embedding()          →  384-dim float vector (sentence-transformers)
        │
        ├──  assign_tag()  →  closest topic: Biology / Physics / CS / ...
        │
        ├──  search_similar()  →  Qdrant ANN search filtered by user_id
        │         Returns: [{text, tag, score}, ...]
        │
        ├──  SQLite: save Question(text, tag, timestamp)
        │
        └──  Qdrant: store_vector(id, embedding, payload)
```

---

## Running Tests

```bash
# From project root
python -m pytest tests/ -v

# Or directly (also exports Excel report)
python tests/test_questions.py
```

The test suite:
- Registers a test user and logs in
- Submits 12 questions across 4 topic clusters
- Verifies topic tagging accuracy (≥70%)
- Validates Qdrant similarity search results
- Confirms user isolation (users only see their own history)
- Exports a styled 3-sheet Excel report: `test_results_<timestamp>.xlsx`

---

## Routes

| Route | Method | Description |
|---|---|---|
| `/` | GET | Dashboard (login required) |
| `/ask` | POST | Submit a question, get similar results |
| `/history` | GET | Browse question history (filter by `?tag=`) |
| `/login` | GET/POST | Login form |
| `/register` | GET/POST | Registration form |
| `/logout` | GET | Logout |

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | Flask session secret |
| `DATABASE_URL` | Yes | SQLite or PostgreSQL URL |
| `QDRANT_URL` | Yes | Qdrant Cloud cluster URL |
| `QDRANT_API_KEY` | Yes | Qdrant API key |
| `QDRANT_COLLECTION` | No | Collection name (default: `gisul_questions`) |
| `EMBEDDING_MODEL` | No | Model name (default: `all-MiniLM-L6-v2`) |
