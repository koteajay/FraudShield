# FraudShield — Explainable Fraud Detection & Reviewer Platform

FraudShield is an explainable fraud detection and investigation platform designed to assess transaction risk, highlight fraudulent patterns with transparent explanations, and provide reviewer workflows.

> **Status: Phase 0 Complete**  
> This repository contains the Phase 0 foundational architecture. Fraud detection engines, database models, rules, risk scoring, and reviewer workflows will be introduced in subsequent phases.

---

## 🛠 Technology Stack

### Backend
- **Language**: Python 3.11+
- **API Framework**: FastAPI
- **ASGI Server**: Uvicorn
- **Validation & Settings**: Pydantic v2 & Pydantic Settings
- **ORM / Database**: SQLAlchemy 2.0 with SQLite (`sqlite:///./fraudshield.db`)
- **Testing**: Pytest & HTTPX TestClient

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
│   ├── app/
│   │   ├── __init__.py        # Backend package marker
│   │   ├── config.py          # Pydantic Settings & environment parsing
│   │   ├── database.py        # SQLAlchemy engine, sessionmaker, & get_db
│   │   └── main.py            # FastAPI app, CORS middleware, /health & /api
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_health.py     # Unit tests for health & db connection
│   ├── requirements.txt       # Minimal backend dependencies
│   ├── .env.example           # Backend environment variable template
│   └── .env                   # Local backend environment file (git-ignored)
│
├── frontend/
│   ├── src/
│   │   ├── components/        # UI components (Header, ConnectionStatusCard, etc.)
│   │   ├── pages/             # Page views (HomePage)
│   │   ├── services/          # API service calling /health & /api
│   │   ├── types/             # TypeScript interfaces
│   │   ├── App.tsx            # Root application component
│   │   ├── index.css          # Tailwind CSS configuration
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

From the root directory:

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

# 2. Install backend dependencies
pip install -r backend/requirements.txt

# 3. Create .env if not already present
cp backend/.env.example backend/.env

# 4. Start the backend development server
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at:
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
- **API Info**: [http://localhost:8000/api](http://localhost:8000/api)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

To run the backend test suite:
```bash
pytest backend/tests
```

---

### 2. Frontend Setup & Run

From the root directory:

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Create .env if not already present
cp .env.example .env

# 4. Start Vite dev server
npm run dev
```

The frontend client will open at:
- [http://localhost:5173](http://localhost:5173)

The page will immediately verify connectivity to the backend by calling `GET /health` and display **"Backend Status: Connected"**.

---

## 🧪 Phase 0 Validation Checklist

- [x] FastAPI starts cleanly and serves `GET /health` returning `{"status": "ok"}`
- [x] `GET /api` returns metadata, service status, and environment
- [x] CORS middleware configured for `http://localhost:5173`
- [x] SQLAlchemy SQLite database engine initializes without errors
- [x] Pytest suite passes 100% of tests (`backend/tests/test_health.py`)
- [x] React/Vite/TypeScript frontend builds with zero errors
- [x] Frontend successfully connects to backend `GET /health` and displays connectivity status
- [x] All `.env` and SQLite `.db` files are strictly excluded via `.gitignore`
- [x] Clean architecture ready for Phase 1
