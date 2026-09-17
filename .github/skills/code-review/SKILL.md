---
name: code-review
description: Conducts an automated architectural and AI-integration code review on recent git changes or specific implementation increments against FastAPI and RAG production standards.
tools: ['read', 'grep', 'glob', 'bash']
---

# Code Review Skill

This skill performs a rigorous code review of recently added or modified code. It acts as a senior reviewer ensuring that the implementation strictly adheres to the project's layered architecture, async conventions, Pydantic type safety, AI guardrails, and proper test mocking before code is merged.

## Inputs

- **Target Code:** Recent git commits (`git diff HEAD~1`), staged changes (`git diff --cached`), or specific files modified during the current increment.
- **Context Files:** `.github/copilot-instructions.md`, `.github/instructions/fastapi-standards.md`, and `TASK.md`.

## When NOT to use

- Do not use when only modifying documentation files (e.g., `README.md`, `TASK.md`, `PLAN.md`) or non-code assets.
- Do not use for initial empty project skeletons that contain no business logic or endpoints.

## Steps

1. **Load Standards:** Review the rules defined in `.github/copilot-instructions.md` and `.github/instructions/fastapi-standards.md`.
2. **Analyze Changes:** Run `git diff` or inspect the modified Python files to understand the scope of the implementation.
3. **Layering & Architecture Check:**
   - Verify that Routers only handle HTTP requests/responses and delegate all business logic (including RAG flows, text chunking, and AI prompting) to Service layers.
   - Verify that database operations use SQLAlchemy 2.0 async syntax (`select()`, `session.execute()`) and are isolated from Routers.
4. **Validation & Type Safety Check:**
   - Ensure explicit Pydantic schemas are used for request bodies and API response models (`response_model=...`).
   - Check that no raw dictionaries or SQLAlchemy ORM models are returned directly by endpoints.
5. **AI & Guardrails Check:**
   - Verify that vector operations use `pgvector.sqlalchemy` operators correctly (e.g., cosine similarity).
   - Ensure external AI calls (Google Gemini) use asynchronous HTTP clients (`httpx.AsyncClient`).
   - Verify that domain exceptions and API rate limits are caught and converted to clean FastAPI `HTTPException` responses without leaking stack traces.
6. **Formatting & Type Safety Check:**
   - Run the local quality tools to ensure no formatting or type issues were introduced:
     ```bash
     black --check backend/
     ruff check backend/
     cd backend && mypy app
     ```
   - Flag any formatting discrepancies or type errors as blocking issues.
7. **Test Coverage Check:**
   - Verify that corresponding automated tests exist in `tests/` for the new code.
   - **CRITICAL:** Ensure that any tests interacting with the AI Service use `respx` (or similar tools) to mock external Google Gemini API calls. No live HTTP calls are allowed during tests.
   - Verify that running `pytest --cov=backend/app` shows no drop in test coverage and meets the minimum project threshold (80%).
8. **Generate Report:** Produce a structured Markdown review report summarizing the findings.

## Output Format

```markdown
## Code Review Report — [Increment Name / Branch]

### Blocking Issues (Must Fix)
- [File/Line]: [Description of architectural violation, e.g., prompt logic in router, sync code in async function, or missing pgvector guardrails]
- [File/Line]: [Missing Pydantic validation or unmocked live AI call in tests]

### Recommendations (Nice to Have)
- [File/Line]: [Suggestion for PEP 8 naming, docstrings, structlog usage, or DB query optimization]

### Test Verification
- [ ] Automated tests accompany the changes.
- [ ] External API calls (Gemini) are properly mocked using `respx`.

### Verdict: [PASS / CHANGE REQUESTED]
[Brief concluding summary of the implementation quality]

### Rules
- Zero Tolerance for Fat Routers: Immediately flag any endpoint that contains direct SQLAlchemy queries, text chunking logic, or prompt formatting inside the route handler.
- No Blocking I/O: Flag any synchronous calls (e.g., requests.post(), time.sleep(), legacy session.query()) inside async def functions as blocking issues.
- No Live AI in Tests: Instantly flag any test file that hits the real Gemini API. respx mocking is mandatory.
- Strict Verdicts: If there is even one "Blocking Issue", the Verdict MUST be CHANGE REQUESTED. Only issue a PASS if all architectural, RAG, and testing constraints are met.
- Actionable Feedback: Always explain why something is wrong and provide a brief snippet showing the correct FastAPI/SQLAlchemy/httpx pattern.
- Code Style & Types Compliance: Code must pass `black --check`, `ruff check`, and `mypy app`. Any linter or type-checking error found via bash must be marked as a blocking issue.
