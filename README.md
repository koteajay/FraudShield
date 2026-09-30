# FraudShield — Explainable Fraud Detection & Reviewer Platform

FraudShield is an explainable fraud detection and investigation platform designed to assess transaction risk, highlight fraudulent patterns with transparent explanations, and provide reviewer workflows.

> **Status: Phase 1 — Backend Foundation Complete**  
> This repository contains the core backend architecture including FastAPI, SQLAlchemy SQLite connection foundation, Alembic migration structure, structured logging, centralized error handling, and health verification.  
> *Application models (User, Transaction, FraudFlag, Device, Review) and fraud engine logic are intentionally reserved for subsequent phases.*

---

## 🛠 Technology Stack

### Backend
- **Language**: Python 3.11+
- **API Framework**: FastAPI
- **ASGI Server**: Uvicorn
- **Validation & Settings**: Pydantic v2 & Pydantic Settings
- **ORM / Database**: SQLAlchemy 2.0 with SQLite (`sqlite:///./fraudshield.db`)
- **Database Migrations**: Alembic
- **Testing**: Pytest & Starlette TestClient (HTTPX)
- **Logging**: Python Standard Library `logging` with structured format

### Frontend
- **Framework**: React 19 + TypeScript
- **Tooling**: Vite
- **Styling**: Tailwind CSS v4
- **Icons**: Lucide React

---

## 📁 Project Structure

```text
fraudshield/
├── backend/
│   ├── alembic/               # Alembic database migration environment
│   │   ├── versions/          # Migration version scripts (for future models)
│   │   ├── env.py             # Alembic migration runner with Base.metadata
│   │   └── script.py.mako
│   ├── app/
│   │   ├── __init__.py        # Backend package marker
│   │   ├── config.py          # Pydantic Settings & environment parsing
│   │   ├── database.py        # SQLAlchemy engine, sessionmaker, get_db, init_db
│   │   ├── logging_config.py  # Structured standard logging configuration
│   │   ├── exceptions.py      # Centralized error handling & sanitization
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   └── health.py      # GET /health & /api/health with DB ping
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── health.py      # HealthResponse & ApiInfoResponse schemas
│   │   │   └── errors.py      # Standardized ErrorResponse schema
│   │   └── main.py            # FastAPI app, lifespan, CORS, middleware
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_health.py     # Comprehensive test suite for Phase 1
│   ├── alembic.ini            # Alembic config for backend directory
│   ├── requirements.txt       # Core backend dependencies
│   ├── .env.example           # Backend environment variable template
│   └── .env                   # Local backend environment file (git-ignored)
│
├── frontend/
│   ├── src/
│   │   ├── components/        # Header, ConnectionStatusCard, ArchitectureCard
│   │   ├── pages/             # HomePage
│   │   ├── services/          # API service calling /health & /api
│   │   ├── types/             # TypeScript interfaces
│   │   ├── App.tsx            # Root application layout
│   │   ├── index.css          # Tailwind CSS styles
│   │   └── main.tsx           # React DOM root entry
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── .env.example           # Frontend environment variable template
│   └── .env                   # Local frontend environment file (git-ignored)
│
├── .gitignore                 # Root gitignore (.env, node_modules, .venv, *.db)
├── .env.example               # Root combined environment template
├── alembic.ini                # Root Alembic configuration
└── README.md                  # Project documentation
```

---

## ⚙️ Environment Configuration

### Backend (`backend/.env`)
```bash
APP_NAME=FraudShield
APP_ENV=development
DATABASE_URL=sqlite:///./fraudshield.db
API_PREFIX=/api
LOG_LEVEL=INFO
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
```

### Frontend (`frontend/.env`)
```bash
VITE_API_BASE_URL=http://localhost:8000
```

---

## 🚀 Running the Project

### 1. Backend Setup & Run

From the repository root:

```bash
# 1. Activate virtual environment
.\.venv\Scripts\Activate.ps1
# On Linux/macOS: source .venv/bin/activate

# 2. Install backend dependencies
cd backend
pip install -r requirements.txt

# 3. Create .env if not present
cp .env.example .env

# 4. Start the FastAPI server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at:
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **API Information**: [http://127.0.0.1:8000/api](http://127.0.0.1:8000/api)
- **Interactive OpenAPI Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Redoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

#### Running Backend Tests
```bash
pytest backend/tests
```

#### Running Database Migrations (Alembic)
```bash
cd backend
alembic current
# To generate a revision in Phase 2+:
# alembic revision --autogenerate -m "create fraud tables"
# alembic upgrade head
```

---

### 2. Frontend Setup & Run

From the repository root:

```bash
cd frontend
npm install
npm run dev
```

The frontend client will open at:
- [http://localhost:5173](http://localhost:5173)

The page verifies connectivity with the backend by requesting `GET /health` and displays:
- **Backend Status: Connected**
- Active Database status: `connected`
- Measured latency and response payload

---

## 🛡️ Error Handling & Logging

All errors return a consistent, standardized JSON contract:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": []
  }
}
```
Internal unhandled errors (500) log full tracebacks to stdout without leaking sensitive stack traces to clients.

---

## 🧪 Phase 1 Acceptance Checklist

- [x] FastAPI starts cleanly and loads configurations via Pydantic Settings
- [x] SQLite database connection initialized safely without dropping or resetting data
- [x] Alembic migration configuration initialized and connected to SQLAlchemy metadata
- [x] Structured logging implemented with configurable `LOG_LEVEL`
- [x] Global error handling returns consistent JSON contracts without leaking stack traces
- [x] `GET /health` verifies app state and executes a lightweight database ping
- [x] Interactive API documentation active at `/docs` and `/redoc`
- [x] 8/8 Pytest tests pass cleanly covering health, database initialization, validation errors, and 500 error sanitization
- [x] Frontend continues to connect seamlessly to `GET /health`
- [x] Zero application models or fraud logic introduced ahead of time
