# Clinical Data TLF Report Generator — SaaS Platform

AI-powered platform for generating clinical trial TLF (Tables, Listings, Figures) reports.
Users upload SAP documents and ADaM datasets via a web UI, and the platform
asynchronously generates professional PDF reports.

## Architecture

```
Browser ──► Next.js (Frontend) ──► FastAPI (Backend) ──► PostgreSQL (Metadata)
                                        │
                                   ┌────┴────┐
                                   │  Redis  │
                                   └────┬────┘
                                        │
                                   ┌────┴────┐
                                   │ Celery  │──► MinIO (File Storage)
                                   │ Worker  │
                                   └─────────┘
```

| Component | Technology |
|-----------|-----------|
| Frontend | Next.js 16 + SuperTokens + shadcn/ui |
| Backend API | FastAPI + SQLAlchemy 2.0 async |
| Database | PostgreSQL 16 with Row-Level Security |
| Task Queue | Celery + Redis |
| File Storage | MinIO (S3-compatible) |
| Auth | SuperTokens (自托管, 支持 Google/GitHub/Microsoft OAuth + 邮箱密码) |
| Analysis | pandas, numpy, pyreadstat, lifelines, reportlab, matplotlib |

## Quick Start

### Prerequisites

- Docker & Docker Compose v2
- Git

### 1. Clone and configure

```bash
git clone <repo-url>
cd clinical-data-process

# Environment is pre-configured with defaults for local dev.
# Check .env for overridable settings.
```

### 2. Start all services

```bash
docker compose up --build
```

This starts 8 services:

| Service | Port | Description |
|---------|------|-------------|
| `postgres` | 5432 | Database |
| `redis` | 6379 | Task queue & cache |
| `minio` | 9000, 9100 | S3-compatible file storage |
| `supertokens` | 3567 | Authentication engine |
| `api` | 8100 | FastAPI backend |
| `worker` | — | Celery worker (2 replicas) |
| `frontend` | 3100 | Next.js web UI |

### 3. Initialize database

```bash
# Run database migrations
docker compose exec api alembic upgrade head
```

### 4. Access the platform

- **Web UI**: http://localhost:3100
- **API docs**: http://localhost:8100/docs
- **MinIO Console**: http://localhost:9100 (user: minioadmin, pass: minioadmin)

### 5. Complete the setup

1. Register a new account at http://localhost:3100/auth/sign-in
2. SuperTokens will handle authentication; a tenant is auto-created on first login
3. Create a study from the dashboard
4. Upload ADaM datasets (`.sas7bdat`) in the Datasets tab
5. Upload SAP document (`.docx`) in the SAP tab — TOC entries are auto-extracted
6. Select TOC entries and generate TLF reports
7. Preview and download generated PDFs

## API Overview

All API endpoints are prefixed with `/api/v1` and require SuperTokens session
authentication (handled transparently via cookies).

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/studies` | GET/POST | List / Create studies |
| `/studies/{id}` | GET/DELETE | Study details / Archive |
| `/studies/{id}/datasets` | GET | List datasets |
| `/studies/{id}/datasets/upload-start` | POST | Get presigned upload URL |
| `/studies/{id}/datasets/upload-complete` | POST | Finalize upload, extract metadata |
| `/studies/{id}/sap/upload-start` | POST | Get presigned SAP upload URL |
| `/studies/{id}/sap/upload-complete` | POST | Finalize SAP, extract TOC |
| `/studies/{id}/sap/toc` | GET | List TOC entries |
| `/studies/{id}/tlf` | GET | List TLF jobs |
| `/studies/{id}/tlf/generate` | POST | Trigger TLF generation |
| `/studies/{id}/tlf/{jobId}` | GET | Job status |
| `/studies/{id}/tlf/{jobId}/download` | GET | Get PDF download URL |

## Supported TLF Types

### Tables (Statistical Analysis)
- **14.1.1.x** — Subject Disposition
- **14.1.2.x** — Demographics
- **14.1.3.x** — Demographics by Site
- **14.1.4.x** — Demographics Summary
- **14.2.x.x** — Efficacy / Survival
- **14.3.1.x** — Adverse Events Summary
- **14.4.x.x** — Laboratory Values
- **14.5.x.x** — Vital Signs

### Figures
- **KM Survival Curves** (OS, PFS) — via lifelines + matplotlib
- **Waterfall Plots** — Best overall response
- **Swimmer Plots** — Treatment duration and response
- **Spider Plots** — Tumor change over time
- **Box Plots** — Laboratory value distributions

### Listings
- **16.2.1.1** — Subject Disposition
- **16.2.1.4** — Death by Subject

## Project Structure

```
backend/
├── api/               # FastAPI routes, schemas, middleware
│   ├── routers/       # studies, datasets, sap, tlf
│   ├── schemas/       # Pydantic models
│   └── middleware/    # Auth middleware (JWT verification)
├── services/
│   ├── analysis/      # Statistical analyzers (disposition, AE, lab, etc.)
│   ├── figures/       # Figure generation (KM plots, waterfall, etc.)
│   ├── pdf/           # PDF generation with reportlab
│   └── listings/      # Patient data listings
├── orchestrator/      # TLF generation pipeline orchestration
├── workers/           # Celery task definitions
├── db/                # SQLAlchemy models, Alembic migrations
├── storage/           # MinIO client wrapper
└── core/              # Config, security, logging

frontend/
├── src/
│   ├── app/           # Next.js App Router pages
│   ├── components/    # React components
│   │   └── studies/   # Study detail, upload, TOC, generator, preview
│   └── ...
```

## Multi-Tenant Data Isolation

- **SuperTokens users** map to **tenants** in the application (1:1)
- **PostgreSQL RLS** (Row-Level Security) isolates data by `tenant_id`
- **MinIO bucket prefix** isolates file storage per tenant
- Auth middleware extracts `user_id` from the SuperTokens session and injects tenant context

## Development

### Local (without Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn backend.api.main:app --reload --port 8100

# Worker
celery -A backend.workers.celery_app worker --loglevel=info --concurrency=1

# Frontend
cd frontend
npm install
npm run dev
```

### Environment Variables

Key configuration via `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_PASSWORD` | `postgres` | PostgreSQL password |
| `SUPERTOKENS_API_KEY` | — | SuperTokens API key |
| `MINIO_ROOT_USER` | `minioadmin` | MinIO access key |
| `MINIO_ROOT_PASSWORD` | `minioadmin` | MinIO secret key |

## Deployment

### Minimum hardware (single server)

| Resource | Requirement |
|----------|------------|
| CPU | 4 cores |
| RAM | 8 GB |
| Disk | 50 GB SSD |
| OS | Ubuntu 22.04 / Debian 12 |

### Production considerations

- Deploy to **Cloud Run** for auto-scaling and zero idle cost
- Use **Neon PostgreSQL** (serverless) instead of self-hosted Postgres
- Use **Google Cloud Storage** (set `STORAGE_BACKEND=gcs`) instead of MinIO
- Use **HTTP worker** (set `WORKER_HTTP_URL`) instead of Celery+Redis
- SuperTokens Core also runs on Cloud Run, connected to Neon PostgreSQL
- Set up automated backups for Neon PostgreSQL

## License

Proprietary — Internal use.
