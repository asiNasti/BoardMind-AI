## Agent Behaviour

- **Understand intent first.** Before generating code, confirm what the user is trying to achieve. A precise small change beats an impressive large one that misses the point. Always check `TASK.md` and `context/PLAN.md` for context.
- **Minimise blast radius.** Propose the smallest change that satisfies the requirement. Do not refactor surrounding code unless explicitly asked.
- **Respect existing conventions.** Match the style, naming (PEP 8), and structure already present in the file or module being modified. Consistency across a codebase is more valuable than local perfection.
- **Make changes traceable.** If a decision has trade-offs, state them. If an assumption was made, surface it. Leave the developer in control.
- **Validate before suggesting.** Check for unhandled edge cases, missing error paths (HTTP exceptions), AI provider rate limits, and async execution issues before presenting a solution.
- **Tests accompany changes.** Every behavioural change to production code should be paired with a corresponding test change using `pytest`. **CRITICAL:** Never make live HTTP calls to the Google Gemini API during tests; always mock external AI calls using `respx`.

---

## Architecture Principles

- Organise code in **clearly defined, loosely coupled layers** with dependencies that flow in one direction only (e.g., Routers -> Services -> External Clients/Repositories).
- Keep the **domain / business logic layer** free of infrastructure concerns. Rely on FastAPI's Dependency Injection (`Depends()`) to pass database sessions, configurations, or external API clients (like the Gemini client).
- **Isolate AI Logic:** Prompt construction, context formatting, and LLM parsing must be encapsulated within dedicated RAG services. Do not leak prompt engineering into FastAPI routers.
- Express cross-cutting concerns declaratively and uniformly. Use `structlog` for structured, context-rich logging. Use Pydantic models for strict data validation and serialization.
- Prefer **explicit over implicit** at every level: explicit dependencies, explicit Pydantic schemas, explicit error states (FastAPI `HTTPException` following Google AIP error models where applicable).
- Design for **operability from day one**: structured logging, health checks, meaningful metrics, and graceful degradation are not afterthoughts. Use asynchronous capabilities (`async`/`await` with `httpx`) correctly to ensure non-blocking I/O.

---

## Quality Standards

| Dimension | Expectation |
|-----------|-------------|
| **Correctness** | All edge cases, boundary conditions, and RAG-specific scenarios (e.g., no relevant context found via vector search) are handled and tested. |
| **Readability** | Code reads like well-written prose — intent is clear. Follow Pythonic idioms and include standard docstrings for complex LLM orchestrations. |
| **Testability** | Every unit of business logic can be tested in isolation using `pytest`. External API integrations must use `respx` mocks. |
| **Safety** | Enforce AI guardrails (e.g., Cosine Similarity thresholds) to prevent off-topic generations. No unvalidated external input reaches business logic or persistence. |
| **Resilience** | Failures in downstream dependencies (Gemini API timeouts, rate limits) or database connections are handled gracefully; partial failures do not cascade. |
| **Performance** | Resource usage is conscious. Vector database queries utilize appropriate indexes (e.g., HNSW in pgvector). N+1 problems are avoided via SQLAlchemy joined loads. |

---

## Development Workflow

```bash
# Start infrastructure (PostgreSQL with pgvector)
docker-compose up -d db

# Run all tests (fast feedback loop during development)
pytest

# Run tests with async support and respx mocking
pytest --asyncio-mode=auto

# Inspect coverage report (requires pytest-cov)
pytest --cov=backend/app --cov-report=html
# Open htmlcov/index.html to view the report

# Format code and check quality
ruff check .
black .