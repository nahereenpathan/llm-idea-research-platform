# IdeaLens — AI-Powered Idea Research & Analysis Platform

**IdeaLens** is a production-oriented, end-to-end AI innovation workspace built for students, researchers, developers, hackathon participants, and entrepreneurs. It enables users to submit up to three ideas for side-by-side comparison, evaluates them across 10 transparent dimensions, identifies the most promising candidate based on configurable criteria, searches real academic papers (OpenAlex, Crossref) and patent databases (USPTO), synthesizes research gaps, produces structured implementation roadmaps, connects with an interactive AI Mentor across 7 modes, drafts and edits research reports, and builds editable 16:9 widescreen PowerPoint presentations with PPTX export.

---

## 1. Key Capabilities & Architecture

- **Multi-Idea Comparison & Dilemma Solver**: Submit 1, 2, or 3 candidate ideas. Evaluates problem significance, target-user clarity, technical feasibility, implementation simplicity, development cost, adoption potential, competitive differentiation, novelty, security/privacy/ethics, and evidence quality.
- **Explainable Transparent Scoring**: Configurable priority weights with dynamic composite scoring ($Score = \frac{\sum w_i S_i}{\sum w_i} \times 10$). Automatically detects statistical parity/ties when two ideas differ by less than 2.0 points rather than inventing an arbitrary winner.
- **Scholarly Literature Discovery**: Live API integration with **OpenAlex** (including automated abstract reconstruction from inverted indexes) and **Crossref**. Save papers, record personal research notes, and generate abstract syntheses.
- **Patent Prior Art Search**: Real **USPTO** PatentsView query adapter with direct Google Patents record links. Includes explicit legal disclaimers.
- **Research Gap Analysis**: Structured synthesis of existing approaches, author limitations, conflicting findings, identified gaps, and suggested hypotheses backed by real citations.
- **Implementation Roadmap & Task Board**: Milestones, MVP scope, custom stack recommendation with technical rationale, database entity schemas, API specifications, and an interactive task tracker with live status updates (`todo` -> `in_progress` -> `done`).
- **AI Mentor**: 7 specialized modes (*Idea, Research, Technical, Product, Business, Validation, Pitch*) with persistent conversation history and project citation linking.
- **Report & Abstract Generator**: 8 reusable templates with an in-browser Markdown editor and 1-click exports to **PDF**, **Microsoft Word (.docx)**, **Markdown (.md)**, and **LaTeX (.tex)**.
- **PowerPoint Presentation Builder**: Interactive slide studio with 16:9 canvas preview, slide thumbnails, add/edit/delete/reorder controls, themes (*Navy Modern, Minimalist Clean, Academic Slate, Startup Cyber*), and export to editable **Microsoft PowerPoint (.pptx)**.
- **Strict Multi-Tenant Security**: Row-level database ownership verification prevents cross-tenant access. JWT bearer authentication with bcrypt password hashing.

---

## 2. Technology Stack

- **Frontend**: React 18 with Vite, Tailwind CSS, React Router DOM v6, Lucide React icons, Axios.
- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0 ORM, Pydantic v2 schemas, Alembic migrations.
- **Document Exporters**: `reportlab` (PDF), `python-docx` (Word), `python-pptx` (PowerPoint), Markdown, LaTeX.
- **Database**: PostgreSQL (production) with automatic SQLite support for zero-dependency local development and automated testing.
- **Background Tasks**: Celery with Redis broker, paired with an asynchronous thread runner fallback for resilient execution without daemon requirements.
- **AI Providers**: Configurable LLM abstraction supporting OpenAI, Google Gemini, and a deterministic Heuristic Fallback engine ensuring complete offline usability.

---

## 3. Quickstart & Windows Development Guide

### Prerequisites
- Python 3.10+ (tested on Python 3.12.6)
- Node.js 18+ (tested on Node.js v24.21.0, npm 11.19.0)
- *(Optional)* Docker Desktop if running PostgreSQL & Redis via Docker Compose.

---

### Step 1: Backend Setup

Open PowerShell or Command Prompt in the repository root:

```powershell
# Navigate to backend directory
cd backend

# (Optional) Create and activate a Python virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run database migrations (builds SQLite idealens.db or PostgreSQL schema)
alembic upgrade head

# Start FastAPI development server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The backend server will run at:
- **API Base URL**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/api/v1/docs`
- **ReDoc Documentation**: `http://127.0.0.1:8000/api/v1/redoc`
- **Health Check**: `http://127.0.0.1:8000/health`

---

### Step 2: Frontend Setup

In a new terminal window:

```powershell
# Navigate to frontend directory
cd frontend

# Install npm packages
npm install

# Start Vite development server
npm run dev
```

The frontend application will run at:
- **Web Application URL**: `http://localhost:5173`

*(Requests to `/api` are automatically proxied to `http://127.0.0.1:8000` via Vite configuration).*

---

### Step 3: (Optional) Running PostgreSQL & Redis with Docker Compose

If you prefer to run PostgreSQL 16 and Redis instead of SQLite:

```powershell
# From the repository root
docker compose up -d
```

This starts:
- **PostgreSQL**: `localhost:5432` (User: `postgres`, Password: `postgrespassword`, DB: `idealens`)
- **Redis**: `localhost:6379`
- **pgAdmin**: `http://localhost:5050` (Email: `admin@idealens.ai`, Password: `adminpassword`)

In `backend/.env`, set:
```ini
DATABASE_URL=postgresql+psycopg2://postgres:postgrespassword@localhost:5432/idealens
```
Then run `alembic upgrade head`.

---

## 4. Running Automated Tests

Run the complete backend test suite:

```powershell
cd backend
pytest -v
```

All 17 automated tests cover:
- User registration, duplicate checks, login, and JWT verification
- Strict multi-tenant isolation (confirming User B cannot access User A's projects)
- Project CRUD and the 3-idea submission constraint
- Scoring engine calculations, custom priority weighting, and tie detection
- OpenAlex abstract decoder and USPTO search adapters
- Academic paper and patent library persistence
- Report generation, markdown editing, and multi-format exports (PDF, DOCX, MD, LaTeX)
- 10-slide PowerPoint generation, slide editing, and PPTX export

To validate the frontend build:
```powershell
cd frontend
npm run build
```

---

## 5. API Endpoints Map (/api/v1)

| Module | Method | Endpoint | Description |
|---|---|---|---|
| **Auth** | `POST` | `/api/v1/auth/register` | Register user & receive JWT token |
| | `POST` | `/api/v1/auth/login` | Authenticate user & receive JWT token |
| | `GET` | `/api/v1/auth/me` | Fetch authenticated user profile |
| **Projects** | `GET` | `/api/v1/projects/` | List user-owned projects |
| | `POST` | `/api/v1/projects/` | Create a new project workspace |
| | `GET` | `/api/v1/projects/{id}` | Get project details (ownership verified) |
| | `PUT` | `/api/v1/projects/{id}` | Update project title / domain |
| | `DELETE` | `/api/v1/projects/{id}` | Delete project & cascade children |
| | `GET` | `/api/v1/projects/dashboard/stats` | Real-time dashboard counts & jobs |
| **Ideas** | `GET` | `/api/v1/projects/{id}/ideas` | List submitted ideas (up to 3) |
| | `POST` | `/api/v1/projects/{id}/ideas` | Submit an idea candidate |
| | `PUT` | `/api/v1/ideas/{id}` | Edit idea fields |
| | `DELETE` | `/api/v1/ideas/{id}` | Remove idea candidate |
| | `POST` | `/api/v1/ideas/{id}/select` | Mark idea as selected active candidate |
| **Evaluation** | `POST` | `/api/v1/projects/{id}/evaluate` | Run 10-dimension assessment |
| | `GET` | `/api/v1/projects/{id}/evaluation` | Get scores, strengths, and risks |
| | `POST` | `/api/v1/projects/{id}/recommendation` | Recalculate rankings with custom weights |
| **Research** | `GET` | `/api/v1/research/papers/search` | Query OpenAlex or Crossref papers |
| | `POST` | `/api/v1/research/projects/{id}/papers/save` | Save paper to reference library |
| | `GET` | `/api/v1/research/projects/{id}/papers` | List saved project papers |
| | `POST` | `/api/v1/research/papers/{id}/summarize` | AI abstract synthesis |
| | `GET` | `/api/v1/research/patents/search` | Query USPTO patent records |
| | `POST` | `/api/v1/research/projects/{id}/patents/save`| Save patent to project |
| **Gaps** | `POST` | `/api/v1/projects/{id}/gaps/generate` | Synthesize research gap report |
| | `GET` | `/api/v1/projects/{id}/gaps` | Retrieve gap analysis |
| **Roadmaps** | `POST` | `/api/v1/projects/{id}/roadmap/generate` | Generate engineering roadmap & stack |
| | `GET` | `/api/v1/projects/{id}/roadmap` | Get implementation roadmap |
| | `PUT` | `/api/v1/projects/{id}/roadmap/tasks/{task_id}` | Update task status (`todo`/`in_progress`/`done`) |
| **AI Mentor** | `GET` | `/api/v1/mentor/conversations` | List user mentor sessions |
| | `POST` | `/api/v1/mentor/conversations` | Create session (7 modes) |
| | `POST` | `/api/v1/mentor/conversations/{id}/messages` | Send message with project context |
| **Reports** | `GET` | `/api/v1/projects/{id}/reports` | List project reports |
| | `POST` | `/api/v1/projects/{id}/reports/generate` | Generate structured report from template |
| | `PUT` | `/api/v1/reports/{id}` | Edit report markdown |
| **Presentations** | `GET` | `/api/v1/projects/{id}/presentations` | List presentation decks |
| | `POST` | `/api/v1/projects/{id}/presentations/generate`| Generate 10-slide deck |
| | `PUT` | `/api/v1/presentations/{id}/slides` | Edit slide content / layout |
| **Exports** | `GET` | `/api/v1/reports/{id}/export?format=pdf\|docx\|md\|latex` | Download report file |
| | `GET` | `/api/v1/presentations/{id}/export?format=pptx` | Download PowerPoint file |
| | `GET` | `/api/v1/projects/{id}/export-all` | Download complete project JSON archive |

---

## 6. Security & Production Readiness Checklist

- **Password Hashing**: Strong bcrypt hashing with salt.
- **JWT Protection**: Tokens signed with HS256 and configurable expiration.
- **Strict Isolation**: Ownership verification decorator on every route.
- **No Hardcoded Secrets**: All credentials and API keys stored in `.env`.
- **Safe Fallbacks**: Works out of the box even when external LLM API keys or Redis servers are unconfigured.
- **CORS Restriction**: Explicitly restricted to configured frontend origins.
- **Input Validation**: Pydantic v2 schemas validate all fields and constraints.
