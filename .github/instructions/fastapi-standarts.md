---
name: FastAPI Production Standards
description: Universal guidelines for FastAPI production code - routers, services, models, and schemas
applyTo: "backend/app/**/*.py"
---

# FastAPI Production Standards

These standards define the rules for writing clean, secure, and maintainable asynchronous Python code using FastAPI, Pydantic, and SQLAlchemy in this repository.

## Design Principles

- **Separation of Concerns:** Strictly follow a layered architecture. Routers handle HTTP transport, Services handle business logic (including RAG flows and LLM orchestration), and Repositories/Models handle database interactions.
- **Dependency Injection:** Use FastAPI's `Depends()` for passing database sessions, current users, and external clients (e.g., `GeminiClient`). Never create global database sessions or global API clients.
- **Type Safety:** Enforce strict Python type hinting (`->`, `list[]`, `dict[]`, `Optional[]`) everywhere. Let Pydantic validate all incoming and outgoing data.
- **Async First:** Ensure all I/O operations (database queries, pgvector searches, and external API calls via `httpx`) are non-blocking and use `async`/`await`.

## Topic: Naming & Readability

- Use `snake_case` for functions, variables, and file names.
- Use `PascalCase` for Pydantic schemas, SQLAlchemy models, and classes.
- API endpoints must use plural nouns and kebab-case, following standard REST conventions inspired by Google AIP design guidelines (e.g., `/api/chat-sessions` instead of `/api/chatSession`).
- Suffix Pydantic schemas explicitly to avoid model collision with ORM entities (e.g., `DocumentCreate`, `DocumentResponse`).

## Topic: Error Handling

- **Never leak infrastructure details:** Do not expose raw SQLAlchemy errors, `pgvector` indexing errors, or Gemini API stack traces to the client.
- Map domain and external exceptions (e.g., "Document not found", "LLM Rate Limit Exceeded", "Invalid PDF format") to standard HTTP status codes (404, 429, 400, 422) using FastAPI's `HTTPException`.
- Handle expected errors at the Service layer and let the Router convert them to `HTTPException`.

## Topic: Database & AI Operations (SQLAlchemy 2.0 & pgvector)

- Use the new SQLAlchemy 2.0 syntax: `session.execute(select(Model))` instead of the legacy `session.query(Model)`.
- Use `Mapped` and `mapped_column` in declarative base models.
- When performing vector searches, ensure you use the appropriate mathematical operators provided by `pgvector.sqlalchemy` (e.g., `Model.embedding.cosine_distance(query_vector)`).

## Anti-patterns

- **Fat Routers:** Writing database queries, chunking logic, or prompt formatting directly inside the FastAPI `@router` function.
- **Synchronous Blocking:** Using synchronous HTTP libraries (like `requests`) for Gemini API calls inside async endpoints. Always use `httpx.AsyncClient`.
- **Implicit Schemas:** Returning raw ORM objects directly or using `dict` instead of strict Pydantic response models.

## Examples (Good vs Bad)

### BAD: Fat Router leaking DB and LLM logic
```python
@router.post("/chat/sessions/{session_id}/messages/")
async def send_message(session_id: int, message_data: dict, db: AsyncSession = Depends(get_db)):
    # Bad: Business logic, external API call, and DB query all stuffed in the router
    if not message_data.get("content"):
        raise HTTPException(status_code=400)
    
    # Bad: Sync call in async function
    response = requests.post("[https://generativelanguage.googleapis.com/v1beta](https://generativelanguage.googleapis.com/v1beta)...", json=...)
    
    new_message = ChatMessage(session_id=session_id, content=response.text)
    db.add(new_message)
    await db.commit()
    return new_message
```

### GOOD: Clean Router delegating to Service
```python
@router.post(
    "/chat/sessions/{session_id}/messages/", 
    response_model=ChatMessageResponse, 
    status_code=status.HTTP_201_CREATED
)
async def create_chat_message(
    session_id: int,
    message_in: ChatMessageCreate, 
    db: AsyncSession = Depends(get_db_session),
    rag_service: RAGService = Depends(get_rag_service)
) -> ChatMessageResponse:
    """
    Good: Router only handles HTTP validation and delegates domain logic 
    (vector search, prompt building, LLM calling) to the RAGService.
    """
    try:
        message = await rag_service.process_user_message(db, session_id, message_in)
        return message
    except SessionNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    except ExternalAPIError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI service unavailable")
```
