# BoardMind AI

## Overview
Build **BoardMind AI**, a Retrieval-Augmented Generation (RAG) web application that helps players resolve complex rules in board games. Users can upload board game rulebooks (PDF format), and the system processes, chunks, and vectorizes the text. A chat interface allows users to ask questions about the rules, and the AI answers strictly based on the uploaded context.

This document outlines the backend API (FastAPI), vector database persistence (PostgreSQL + pgvector), AI integration (Google Gemini API), and a React frontend. Focus areas: accurate text chunking, efficient vector search (cosine similarity), strict AI guardrails (answering ONLY based on the context), and Docker-based deployment.

---

## Tech Stack
| Layer | Technology / Approach |
| --- | --- |
| Backend | Python 3.11+, FastAPI, Pydantic, SQLAlchemy 2.0+ (async), Alembic |
| Database | PostgreSQL with `pgvector` extension (Dockerized). `alembic` for migrations. |
| AI API | Google Gemini API (`text-embedding-004` for vectors, `gemini-1.5-flash` for chat) |
| API Docs | FastAPI OpenAPI (Swagger UI / Redoc) |
| Frontend | React.js, responsive chat interface, markdown rendering |
| DevOps | Docker, docker-compose (services: app, db, frontend) |
| Testing | pytest, pytest-asyncio, httpx, `respx` (for mocking Google Gemini API) |

---

## Domain Model
Main entities and brief attributes (ORM-focused):

- `Game`: id, title, description, created_at, updated_at
- `Document`: id, game_id (FK), filename, uploaded_at
- `DocumentChunk`: id, document_id (FK), content (text), embedding (pgvector Vector), chunk_index
- `ChatSession`: id, game_id (FK), created_at
- `ChatMessage`: id, session_id (FK), role (user | assistant), content, created_at

Implement models using SQLAlchemy ORM (async sessions), and Pydantic models for API input/output.

---

## Business Rules & AI Guardrails

1. **Document Upload:** Only `.pdf` files are allowed.
2. **Chunking Strategy:** PDF text must be extracted and split into chunks of ~500-800 characters with a ~100-character overlap to preserve context.
3. **Embeddings:** Each text chunk is sent to the Gemini API (`text-embedding-004`) to generate a vector array.
4. **Vector Search:** When a user asks a question, the query is vectorized. The system queries PostgreSQL using `pgvector` (Cosine Similarity) to find the top 3-5 most relevant `DocumentChunk` records.
5. **Similarity Threshold (Guardrail 1):** If the cosine distance of the closest chunk is too high (meaning the question is unrelated to the rules), the backend must reject the query before calling the LLM, returning a default message: "This question is unrelated to the game rules."
6. **System Prompt (Guardrail 2):** The prompt sent to `gemini-1.5-flash` MUST strictly instruct the model to act as a board game referee and answer *only* based on the provided context chunks. It must say "The rules do not mention this" if the context doesn't contain the answer.
7. **Chat History:** The RAG system should include the last 3-5 messages of the `ChatSession` to maintain conversational context.

---

## RAG Data Flows
**Ingestion Flow (PDF Upload):**
`Upload PDF` → `Extract Text (pdfplumber/PyMuPDF)` → `Split into Chunks` → `Call Gemini Embedding API` → `Store Chunks & Vectors in PostgreSQL`

**Query Flow (Chat):**
`Receive Question` → `Call Gemini Embedding API` → `PostgreSQL Vector Search (Cosine Similarity)` → `Format Prompt with Context + History` → `Call Gemini LLM API` → `Save Messages` → `Return Answer`

Ensure business logic is kept in a `services` layer, not directly in FastAPI routers.

---

## Backend API Design (FastAPI)
Use RESTful endpoints returning JSON. Keep the routing structure flat (routers included directly in `main.py`).

### Endpoints

**Games & Documents**
- `GET /api/games/` - List all games
- `POST /api/games/` - Create a new game
- `POST /api/games/{game_id}/documents/` - Upload a PDF rulebook (triggers Ingestion Flow)

**Chat & RAG**
- `POST /api/chat/sessions/` - Create a new chat session for a specific game
- `GET /api/chat/sessions/{session_id}/messages/` - Get chat history
- `POST /api/chat/sessions/{session_id}/messages/` - Send a question and get an AI answer. Body: `{"content": "How does this card work?"}`

### API behavior
- Use Pydantic models for request validation.
- The chat endpoint can be synchronous (returning standard JSON) or use Server-Sent Events (SSE) for streaming the AI response (optional but preferred).

---

## Data Model and Persistence
Schema design (high level):

- `games` (`id`, `title`, `description`, `created_at`, `updated_at`)
- `documents` (`id`, `game_id`, `filename`, `uploaded_at`)
- `document_chunks` (`id`, `document_id`, `content`, `embedding` VECTOR(768), `chunk_index`)
- `chat_sessions` (`id`, `game_id`, `created_at`)
- `chat_messages` (`id`, `session_id`, `role`, `content`, `created_at`)

Implementation notes:
- Use `pgvector.sqlalchemy` for the `embedding` column type.
- Ensure the vector dimension matches the Gemini embedding model output size (typically 768 for `text-embedding-004`).
- Use Alembic for migrations.
- Create an HNSW or IVFFlat index on the `embedding` column for faster vector search if the dataset grows.

---

## Frontend
A simple, responsive React application.

**Main Views:**
1. **Sidebar/Dashboard:** List of available games. Button to "Add Game & Upload Rules".
2. **Upload Modal:** Form to create a game and upload a `.pdf` file. Display a loading spinner during the ingestion process.
3. **Chat Interface:**
- Message history (User messages aligned right, AI aligned left).
- Input field with a "Send" button.
- Render markdown in AI responses (for bold text, lists, etc.).
- Error handling for off-topic questions.

---

## Testing
- **Unit tests:** `pytest` for the chunking logic and RAG prompt formatting.
- **API Mocks:** Use `respx` to mock HTTP calls to the Google Gemini API. DO NOT make real API calls to Google during automated testing.
- **Integration tests:** `pytest-asyncio` + `httpx.AsyncClient` to test FastAPI endpoints using a test database.

---

## DevOps and Deployment
- Provide a `Dockerfile` for the FastAPI backend and a `Dockerfile` for the React frontend.
- Provide `docker-compose.yml` that includes:
  - `db`: Uses image `pgvector/pgvector:pg16`
  - `backend`: Runs Uvicorn.
  - `frontend`: Runs Node/Nginx for React.
- Pass `GEMINI_API_KEY` and `DATABASE_URL` via a `.env` file (loaded via Pydantic `BaseSettings`).

---

## Delivery Notes
- **Project Structure:** `backend/app/routers/`, `backend/app/services/`, `backend/app/models.py`, `backend/app/database.py`, `backend/tests/`. Keep it simple, no deep nesting.
- **Separation of Concerns:** Keep Gemini API calls wrapped in a dedicated client class inside `services/gemini_client.py`.
- **Error Handling:** Handle PDF extraction errors, API rate limits from Gemini, and invalid file formats gracefully. Return HTTP 400 or 422 with clear messages.