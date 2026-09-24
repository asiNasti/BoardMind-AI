# Implementation Plan — BoardMind AI (FastAPI + RAG)


## Overview

**Goal:** Deliver a production-ready Retrieval-Augmented Generation (RAG) web application that helps players resolve complex rules in board games using PostgreSQL (pgvector), Google Gemini API, and a React frontend.

**Scope (in):**
- Backend service in Python/FastAPI for Games, Documents, DocumentChunks, and Chat.
- PostgreSQL schema via SQLAlchemy + Alembic migrations, utilizing the `pgvector` extension.
- Integration with Google Gemini API (`text-embedding-004` and `gemini-1.5-flash`).
- PDF text extraction and chunking pipeline (Ingestion Flow).
- Vector search (cosine similarity) with strict AI guardrails (Query Flow).
- React frontend for uploading rulebooks and chatting.
- Docker/Docker Compose local runtime for the full stack.
- Automated tests with pytest, pytest-asyncio, httpx, and respx (for Gemini API mocking).

**Scope (out):**
- User authentication and authorization (RBAC).
- Payment or billing integrations.
- Production cloud deployment (Terraform/Kubernetes).
- Advanced OCR for scanned PDFs (assumes text-searchable PDFs).

**Source of truth:** `TASK.md` sections Overview, Tech Stack, Domain Model, Business Rules, RAG Data Flows, Backend API Design, Data Model and Persistence, Testing, DevOps and Deployment.

---

## Architecture Notes

- Layering: FastAPI Routers -> Services (RAG, Ingestion, Gemini API) -> SQLAlchemy ORM models.
- Validation boundary: Pydantic request/response schemas at API layer; domain validations in services.
- Persistence: PostgreSQL with SQLAlchemy async sessions and `pgvector`; schema changes only through Alembic.
- AI Integration: Google Gemini API is accessed via a dedicated asynchronous client service. NO live HTTP calls to Gemini are allowed during tests (must use `respx`).
- Guardrails: Similarity threshold must be checked *before* invoking the LLM. System prompts must enforce strict context adherence.
- Observability: Structured logs, error mapping to FastAPI `HTTPException`.
- Testing strategy: Unit tests for chunking/prompts, `respx` for external AI calls, integration API tests via `httpx.AsyncClient`.

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Gemini API rate limits / timeouts | high | medium | Implement retry logic with exponential backoff; graceful error handling in UI |
| Poor text extraction from complex PDFs | medium | high | Use robust libraries (`pdfplumber` / `PyMuPDF`); chunk with overlap |
| Vector search performance degrades | low | medium | Add HNSW or IVFFlat index to the embedding column in PostgreSQL |
| Live API calls bleeding into test suite | medium | high | Add strict `respx` mock enforcement in pytest fixtures |

---

## Success Criteria (project-level)

- [ ] All increments below have status `completed`.
- [ ] Full test suite green with `pytest`, including async tests and `respx` AI mocks.
- [ ] Coverage is >= 80% for backend modules.
- [ ] `docker-compose up` starts API, DB (with pgvector), and Frontend; `/docs` is reachable.
- [ ] `alembic upgrade head` creates schema successfully on a clean database.
- [ ] Ingestion Flow works: PDF uploaded -> chunked -> vectorized -> stored in DB.
- [ ] Query Flow works: User asks question -> vector search -> LLM answers strictly based on rules.
- [ ] Off-topic questions are rejected by the similarity threshold or LLM guardrail.

---

## Increments

> Each increment is **one vertical slice, one concern, independently testable**.
> Status values: `pending` · `in_progress` · `completed` · `blocked`.

---

### Increment 1 — Project Skeleton and Runtime Baseline

- **Status:** completed
- **Depends on:** none
- **Estimated size:** S

**Goal**

Create a runnable FastAPI service skeleton with Docker infrastructure (including Postgres + pgvector), environment configuration, and local startup path.

**Scope**
- In:
  - Create backend package layout (`app`, `app/api`, `app/db`, `app/services`, `tests`).
  - Add FastAPI app bootstrap and health endpoint.
  - Setup `docker-compose.yml` with `pgvector/pgvector:pg16`.
- Out:
  - Database schema models and AI integrations.

**Files to create / modify**

| File | Action | Purpose |
|------|--------|---------|
| `backend/requirements.txt` | create | Declare runtime/test dependencies |
| `backend/app/main.py` | create | FastAPI app entrypoint |
| `backend/app/api/routers/health.py` | create | Health router |
| `docker-compose.yml` | create | Local service orchestration (DB + API) |
| `.env.example` | create | Template for config variables |

**Tasks (ordered)**
1. Create backend package layout and app factory.
2. Add `/health` baseline availability.
3. Configure `docker-compose.yml` with pgvector image.
4. Add minimal startup check test.

**Expected outputs (interfaces / contracts)**
- Health endpoint contract: `GET /health -> {"status": "ok"}`.
- `docker-compose up` starts the API and DB successfully.

**Acceptance criteria**
- [ ] App starts locally and `/health` returns 200.
- [ ] PostgreSQL container with pgvector runs successfully.
- [ ] `pytest` runs and includes a passing app bootstrap test.

**Notes for implementer**
Keep module imports lightweight to avoid side effects during tests.

---

### Increment 2 — Database Core and Alembic Baseline

- **Status:** completed
- **Depends on:** Increment 1
- **Estimated size:** S

**Goal**

Introduce SQLAlchemy async engine/session management and Alembic baseline migration tooling for PostgreSQL with the `pgvector` extension enabled.

**Scope**
- In:
  - DB settings, async engine, session dependency.
  - Alembic initialization and first baseline migration (CREATE EXTENSION vector).
- Out:
  - Domain tables (Games, Documents).

**Files to create / modify**

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/db/database.py` | create | Async engine/session factory |
| `backend/app/db/base.py` | create | Declarative base metadata |
| `backend/alembic.ini` | create | Alembic config |
| `backend/alembic/env.py` | create | Migration environment setup |
| `backend/alembic/versions/*_enable_pgvector.py`| create | Baseline migration |

**Tasks (ordered)**
1. Add async DB session factory and FastAPI dependency.
2. Configure Alembic to discover SQLAlchemy metadata.
3. Write raw SQL migration to enable pgvector extension.
4. Add DB connectivity smoke test.

**Expected outputs (interfaces / contracts)**
- `get_db_session()` dependency yielding `AsyncSession`.
- `pgvector` extension activated in the target database.

**Acceptance criteria**
- [ ] `alembic upgrade head` succeeds and enables the vector extension.
- [ ] API can resolve DB session dependency without errors.

**Notes for implementer**
Use SQLAlchemy 2.x style and typed `Mapped[]` fields.

---

### Increment 3 — Gemini API Client Service

- **Status:** completed
- **Depends on:** Increment 1
- **Estimated size:** S

**Goal**

Implement the AI client wrapper for Google Gemini API using `httpx.AsyncClient` to handle embeddings and LLM chat requests.

**Scope**
- In:
  - `GeminiClient` class for embeddings and text generation.
  - Setup `respx` for mocking.
- Out:
  - RAG prompt formatting and DB history.

**Files to create / modify**

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/services/gemini_client.py` | create | HTTP wrapper for Gemini API |
| `backend/app/core/config.py` | create | Load GEMINI_API_KEY |
| `backend/tests/services/test_gemini_client.py`| create | Test client using respx mocks |

**Tasks (ordered)**
1. Setup Pydantic `BaseSettings` for API key.
2. Implement async wrapper for `text-embedding-004`.
3. Implement async wrapper for `gemini-1.5-flash`.
4. Write mocked `respx` tests for both endpoints.

**Expected outputs (interfaces / contracts)**
- `generate_embeddings(text: str) -> list[float]`
- `generate_response(prompt: str) -> str`

**Acceptance criteria**
- [ ] Client properly formats REST requests to Gemini.
- [ ] All tests use `respx`; zero live network calls.
- [ ] Graceful handling of timeouts and API errors.

**Notes for implementer**
Do not use the official SDK if it relies on blocking sync requests; use raw HTTP with `httpx.AsyncClient`.

---

### Increment 4 — Game and Document Core (CRUD)

- **Status:** completed
- **Depends on:** Increment 2
- **Estimated size:** M

**Goal**

Implement the foundational domain models and CRUD endpoints for Games and Documents.

**Scope**
- In:
  - `Game` and `Document` ORM models + migrations.
  - Pydantic schemas, routing, and basic services.
- Out:
  - PDF file processing.

**Files to create / modify**

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/db/models.py` | modify | Add Game and Document models |
| `backend/alembic/versions/*_create_games.py` | create | Migration for Games/Documents |
| `backend/app/api/schemas.py` | create | Request/response DTOs |
| `backend/app/api/routers/games.py` | create | Game endpoints |
| `backend/tests/api/test_games.py` | create | API integration tests |

**Tasks (ordered)**
1. Create Game/Document models and generate migrations.
2. Create Pydantic validation schemas.
3. Implement endpoints for listing/creating games.
4. Write DB transactional API tests.

**Expected outputs (interfaces / contracts)**
- `GET /api/games/`, `POST /api/games/`
- `GET /api/games/{game_id}/documents/`

**Acceptance criteria**
- [ ] Endpoints validate inputs using Pydantic.
- [ ] DB correctly stores and retrieves Game metadata.

**Notes for implementer**
Ensure routers delegate DB operations to a service layer.

---

### Increment 5 — RAG Ingestion Flow (PDF Processing)

- **Status:** completed
- **Depends on:** Increment 3, Increment 4
- **Estimated size:** L

**Goal**

Implement the PDF upload, text extraction, chunking, and embedding generation pipeline.

**Scope**
- In:
  - `DocumentChunk` model (with Vector column).
  - PDF parsing logic and chunker.
  - Upload endpoint `POST /api/games/{id}/documents/`.
- Out:
  - Async task queues (process synchronously for MVP).

**Files to create / modify**

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/db/models.py` | modify | Add DocumentChunk model |
| `backend/alembic/versions/*_create_chunks.py` | create | Migration (Vector column size 768) |
| `backend/app/services/pdf_parser.py` | create | Text extraction and chunking |
| `backend/app/services/ingestion_service.py` | create | Orchestrates parsing + DB |
| `backend/app/api/routers/documents.py` | create | Upload endpoint |
| `backend/tests/services/test_ingestion.py` | create | Unit tests for chunking |

**Tasks (ordered)**
1. Add `DocumentChunk` model with pgvector Vector type.
2. Write text extraction and overlap chunking logic.
3. Wire extraction output to `GeminiClient` embeddings.
4. Save chunks and vectors to DB.

**Expected outputs (interfaces / contracts)**
- Chunker splits text at ~500-800 chars with ~100 char overlap.
- `POST` endpoint returns 201 Created.

**Acceptance criteria**
- [ ] PDF upload extracts text successfully.
- [ ] Chunks are stored in PostgreSQL with corresponding embeddings.
- [ ] Mocks are used for Gemini embedding calls in tests.

**Notes for implementer**
Handle invalid file formats gracefully returning 400.

---

### Increment 6 — Chat Sessions & Messages (CRUD)

- **Status:** pending
- **Depends on:** Increment 4
- **Estimated size:** M

**Goal**

Create data structures and endpoints to manage chat history for a specific game.

**Scope**
- In:
  - `ChatSession` and `ChatMessage` models + migrations.
  - Endpoints to create session and fetch history.
- Out:
  - LLM generation logic.

**Files to create / modify**

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/db/models.py` | modify | Add ChatSession, ChatMessage |
| `backend/alembic/versions/*_create_chat.py` | create | Migration for chat tables |
| `backend/app/api/routers/chat.py` | create | Session/history endpoints |
| `backend/tests/api/test_chat.py` | create | API integration tests |

**Tasks (ordered)**
1. Create Chat models and migrations.
2. Implement session creation endpoint.
3. Implement message history retrieval endpoint.
4. Add API tests.

**Expected outputs (interfaces / contracts)**
- `POST /api/chat/sessions/`
- `GET /api/chat/sessions/{session_id}/messages/`

**Acceptance criteria**
- [ ] Chat sessions are correctly linked to a Game.
- [ ] History returns ordered list of user and assistant messages.

**Notes for implementer**
Return messages sorted by `created_at` ascending.

---

### Increment 7 — RAG Query Flow & Guardrails

- **Status:** completed
- **Depends on:** Increment 5, Increment 6
- **Estimated size:** L

**Goal**

Implement vector search, similarity threshold checking, prompt generation, and LLM invocation.

**Scope**
- In:
  - Vector search using `pgvector` Cosine Similarity.
  - Guardrail 1 (Similarity rejection) & Guardrail 2 (System prompt).
  - Chat message POST endpoint.
- Out:
  - Streaming responses (SSE).

**Files to create / modify**

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/services/rag_service.py` | create | Search, guardrails, LLM orchestration |
| `backend/app/api/routers/chat.py` | modify | Add POST message endpoint |
| `backend/tests/services/test_rag_service.py` | create | Tests for guardrails |

**Tasks (ordered)**
1. Vectorize user query via `GeminiClient`.
2. Execute Cosine Similarity search in Postgres.
3. Apply similarity threshold check.
4. Format system prompt with chunks and chat history.
5. Save user and AI responses to DB.

**Expected outputs (interfaces / contracts)**
- `POST /api/chat/sessions/{id}/messages/` -> returns AI answer.

**Acceptance criteria**
- [x] Vector search returns top 3-5 closest chunks.
- [x] Requests below similarity threshold bypass LLM and return default message.
- [x] User and Assistant messages are saved to the database.

**Notes for implementer**
Use SQLAlchemy `cosine_distance` operator correctly.

---

### Increment 8 — Frontend Skeleton & Game Management

- **Status:** pending
- **Depends on:** Increment 4, Increment 5
- **Estimated size:** M

**Goal**

Bootstrap the React frontend and build the UI for listing games and uploading PDF rulebooks.

**Scope**
- In:
  - React setup and API service layer.
  - Sidebar with games list.
  - Upload Modal with loading state.
- Out:
  - Chat UI.

**Files to create / modify**

| File | Action | Purpose |
|------|--------|---------|
| `frontend/package.json` | create | Frontend dependencies |
| `frontend/src/services/api.js` | create | Axios/fetch client |
| `frontend/src/components/Sidebar.jsx` | create | List games |
| `frontend/src/components/UploadModal.jsx` | create | PDF upload form |

**Tasks (ordered)**
1. Initialize React app.
2. Create API client for backend communication.
3. Build Sidebar component.
4. Build Upload Modal component.

**Expected outputs (interfaces / contracts)**
- Running frontend application.

**Acceptance criteria**
- [ ] User can view a list of games.
- [ ] User can create a new game and upload a `.pdf` file.
- [ ] Loading spinner displays during ingestion process.

**Notes for implementer**
Use standard FormData for PDF uploads.

---

### Increment 9 — Frontend Chat Interface

- **Status:** pending
- **Depends on:** Increment 6, Increment 7, Increment 8
- **Estimated size:** M

**Goal**

Build the conversational UI allowing users to ask questions about the selected game.

**Scope**
- In:
  - Chat window, message history, input field.
  - Markdown rendering.
- Out:
  - Real-time typing animation (unless SSE is implemented).

**Files to create / modify**

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/components/ChatWindow.jsx` | create | Message display and input |
| `frontend/src/components/MarkdownView.jsx` | create | Render markdown safely |

**Tasks (ordered)**
1. Build chat layout.
2. Fetch and display session history on game selection.
3. Wire up message sending and response handling.
4. Add Markdown support.

**Expected outputs (interfaces / contracts)**
- Fully functional chat interface bound to selected game's session.

**Acceptance criteria**
- [ ] User can send a message and see it appear.
- [ ] AI response is appended and rendered with Markdown.

**Notes for implementer**
Ensure auto-scroll to bottom on new messages.

---

### Increment 10 — Final Verification and Dockerization

- **Status:** pending
- **Depends on:** Increment 1-9
- **Estimated size:** S

**Goal**

Finalize operational baseline, ensure full stack runs seamlessly via Docker Compose, and verify E2E behavior.

**Scope**
- In:
  - `Dockerfile` for backend and frontend.
  - Final `docker-compose.yml`.
  - README updates.
- Out:
  - Cloud deployment.

**Files to create / modify**

| File | Action | Purpose |
|------|--------|---------|
| `backend/Dockerfile` | create | API container image |
| `frontend/Dockerfile` | create | React container image |
| `docker-compose.yml` | modify | Add frontend service |
| `README.md` | modify | Run/test instructions |

**Tasks (ordered)**
1. Write Dockerfiles.
2. Wire all services in `docker-compose.yml`.
3. Test fresh build from scratch.
4. Update `README.md`.

**Expected outputs (interfaces / contracts)**
- One-command local stack startup via `docker-compose up`.

**Acceptance criteria**
- [ ] `docker-compose up` starts Postgres, FastAPI, and React simultaneously.
- [ ] RAG flow works accurately with a real board game PDF.

**Notes for implementer**
Ensure backend and frontend can communicate over Docker networking.
