# AI Chat Application

A full-stack web application for chatting with AI models via OpenRouter API, featuring real-time streaming responses, automatic message summarization for long conversations, and per-user chat history management.

## Architecture Overview

### Stack
- **Frontend**: Next.js 16 (App Router), React, TypeScript, Tailwind CSS, Zustand, TanStack Query
- **Backend**: FastAPI (Python 3.12), SQLAlchemy, Alembic, PostgreSQL
- **LLM**: OpenRouter API (free models: `google/gemma-3-27b-it:free`)
- **Infrastructure**: Docker + Docker Compose

### Key Features
✅ Real-time SSE streaming for AI responses  
✅ Automatic context summarization for long conversations (>30 messages)  
✅ Per-user chat history with anonymous client IDs (no authentication)  
✅ Auto-generated chat titles from first message  
✅ Markdown rendering with syntax highlighting  
✅ Dark/light theme support  
✅ Fully responsive UI  

## Quick Start

### Prerequisites
- Docker & Docker Compose OR
- Node.js 20+, Python 3.12+, PostgreSQL 16

### Option 1: Docker (Recommended)

```bash
# Clone and enter project
cd ai_chat_task

# Create backend env for Docker Compose
cp backend/.env.example backend/.env
# Edit backend/.env and set at least OPENROUTER_API_KEY
# For Docker Compose keep POSTGRES_HOST=postgres and BACKEND_URL=http://backend:8000

# Start all services
docker compose up

# Access:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs (Swagger UI)
```

### Option 2: Local Development

#### Backend Setup
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your OpenRouter API key and PostgreSQL credentials
# For local backend runs set POSTGRES_HOST=localhost

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

#### Frontend Setup
```bash
cd frontend

# Optional: configure backend target for the internal BFF route
cat > .env.local << EOF
BACKEND_URL=http://localhost:8000
EOF

# Install dependencies
npm install

# Start dev server
npm run dev

# Access: http://localhost:3000
```

## Environment Variables

### Backend (.env)
```
OPENROUTER_API_KEY=sk-your-key-here
OPENROUTER_API_URL=https://openrouter.ai/api/v1/chat/completions
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ai_chat_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=1234
MODEL_NAME=openai/gpt-oss-20b:free
MESSAGE_THRESHOLD=30
RECENT_MESSAGES_KEPT=20
SUMMARY_BATCH_SIZE=10
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173"]
RATE_LIMIT=60/minute
BACKEND_URL=http://localhost:8000
```

### Key Configuration
- `POSTGRES_HOST`: Use `postgres` in Docker Compose and `localhost` for local backend runs
- `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`: Discrete PostgreSQL connection settings used by both the app and Alembic
- `MESSAGE_THRESHOLD`: Trigger summarization after N unsummarized messages
- `RECENT_MESSAGES_KEPT`: Number of recent messages always sent to LLM
- `SUMMARY_BATCH_SIZE`: Number of oldest messages to summarize at once

### Frontend (.env.local)
```
BACKEND_URL=http://localhost:8000
```

- `BACKEND_URL`: Server-side target used by Next.js route handlers to proxy `/api/v1/*` to FastAPI.
- In Docker Compose, the frontend reads `BACKEND_URL=http://backend:8000` from `backend/.env`.

## Project Structure

```
ai_chat_task/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI factory
│   │   ├── api/v1/
│   │   │   ├── chats.py            # Chat CRUD endpoints
│   │   │   └── messages.py         # Message + SSE streaming
│   │   ├── services/
│   │   │   ├── llm_service.py      # OpenRouter client
│   │   │   ├── context_service.py  # Summarization logic
│   │   │   ├── chat_service.py     # Chat business logic
│   │   │   └── message_service.py  # Message orchestration
│   │   ├── repositories/           # Data access layer
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   ├── schemas/                # Pydantic request/response
│   │   └── core/
│   │       ├── config.py           # Settings
│   │       ├── database.py         # AsyncSession setup
│   │       └── dependencies.py     # Dependency injection
│   ├── alembic/                    # Database migrations
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── api/v1/[...path]/route.ts  # BFF proxy to FastAPI
│   │   ├── layout.tsx                 # Root layout + providers
│   │   ├── page.tsx                   # Root redirect
│   │   └── chat/
│   │       ├── page.tsx               # New chat page
│   │       └── [id]/page.tsx          # Chat view
│   ├── src/
│   │   ├── widgets/
│   │   │   ├── sidebar/            # Chat navigation
│   │   │   └── chat-area/          # Main chat interface
│   │   ├── features/
│   │   │   └── send-message/       # Message sending + streaming
│   │   ├── entities/
│   │   │   ├── chat/               # Chat models, API, UI
│   │   │   └── message/            # Message models, API, UI
│   │   └── shared/
│   │       ├── api/                # HTTP client
│   │       ├── lib/                # Utilities
│   │       ├── ui/                 # Shared components
│   │       └── providers/          # React providers
│   └── package.json
│
└── docker-compose.yml
```

## API Endpoints

All endpoints require `X-Client-Id: <uuid>` header for data isolation.

```
GET    /api/v1/chats                    List user's chats
POST   /api/v1/chats                    Create new chat
GET    /api/v1/chats/{id}               Get single chat
DELETE /api/v1/chats/{id}               Delete chat

GET    /api/v1/chats/{id}/messages      Get chat messages
POST   /api/v1/chats/{id}/messages      Send message (SSE stream)
```

### Example: Send Message with cURL

```bash
export CLIENT_ID=$(uuidgen)

curl -X POST http://localhost:8000/api/v1/chats/123/messages \
  -H "X-Client-Id: $CLIENT_ID" \
  -H "Content-Type: application/json" \
  -d '{"content": "What is the capital of France?"}' \
  -N
```

Response (Server-Sent Events):
```
data: {"type": "delta", "content": "The"}
data: {"type": "delta", "content": " capital"}
data: {"type": "done", "message_id": "uuid", "content": "The capital of France is Paris."}
```

## Context Management

The system automatically manages LLM context window to prevent token overflow:

### Summarization Strategy
1. **Trigger**: When unsummarized messages > `MESSAGE_THRESHOLD` (default: 30)
2. **Batch**: Summarize oldest `SUMMARY_BATCH_SIZE` messages (default: 10)
3. **Preserve**: Keep last `RECENT_MESSAGES_KEPT` messages (default: 20) in active context
4. **Storage**: Accumulated summaries stored in `chats.summary` field

### Flow
```
[Active Messages] (recent N messages)
        ↓
[Summary] (from older messages)
        ↓
[System Prompt]
        ↓
[LLM Request]
```

## Database Schema

### chats
- `id` (UUID): Primary key
- `client_id` (UUID): Anonymous user identifier (indexed)
- `title` (VARCHAR 255, nullable): Chat title (null = auto-generating)
- `created_at`, `updated_at` (DATETIME)
- `summary` (TEXT, nullable): Accumulated message summaries
- `message_count` (INTEGER): Denormalized count

### messages
- `id` (UUID): Primary key
- `chat_id` (UUID FK): Reference to chat
- `role` (VARCHAR 20): "user" or "assistant"
- `content` (TEXT): Message body
- `created_at` (DATETIME)
- `is_summarized` (BOOLEAN): False = active context, True = included in summary

## Frontend Architecture

### Technology Stack
- **State Management**:
  - Zustand: ephemeral streaming state
  - TanStack Query: server state, optimistic message updates, cache invalidation
- **Networking**: same-origin `/api/v1/*` requests proxied by a Next.js route handler to FastAPI
- **Styling**: Tailwind CSS + dark mode via next-themes
- **Code Organization**: Feature-Sliced Design (FSD)

### Component Hierarchy
```
RootLayout (providers)
├── page.tsx (redirect logic)
└── chat/
    ├── page.tsx (new chat)
    └── [id]/page.tsx
        ├── Sidebar
        │   ├── ChatListItem[]
        │   └── ThemeToggle
        └── ChatArea
            ├── MessageFeed
            │   ├── MessageBubble[]
            │   └── StreamingCursor
            └── MessageInput
```

### Data Flow
1. User types message → MessageInput
2. React Query writes optimistic user/assistant placeholders into the chat cache
3. Client opens an SSE request to `/api/v1/chats/{id}/messages`
4. Next.js proxies the request to FastAPI via `BACKEND_URL`
5. Stream chunks update the optimistic assistant message in cache
6. On completion, chats/messages queries are invalidated and reconciled with server data

## Getting an OpenRouter API Key

1. Visit https://openrouter.ai/
2. Sign up with email or OAuth
3. Go to Keys page and create new key
4. Copy the key and paste into `.env`

Free tier includes access to many models including `google/gemma-3-27b-it:free`

## Testing

### Manual E2E Flow

```bash
# 1. Start services
docker compose up

# 2. Create chat
curl -X POST http://localhost:8000/api/v1/chats \
  -H "X-Client-Id: $(uuidgen)" \
  -H "Content-Type: application/json" \
  -d '{}'

# 3. Send message (note: -N flag enables streaming)
curl -X POST http://localhost:8000/api/v1/chats/{chat_id}/messages \
  -H "X-Client-Id: {client_id}" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello!"}' \
  -N

# 4. Visit http://localhost:3000 in browser
```

## Development

### Common Commands

**Backend**:
```bash
cd backend

# Run in dev mode with auto-reload
uvicorn app.main:app --reload

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Check migrations status
alembic current

# Run tests (if added)
pytest
```

**Frontend**:
```bash
cd frontend

# Start dev server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint and format
npm run lint
npm run format
```

## Known Limitations

- Anonymous users (no login required, but no data persistence across devices)
- Single LLM model at a time (could add model selection)
- No file upload support
- Context summarization is rule-based (not ML-based)
- No real-time collaboration (single user per chat)

## Future Enhancements

- [ ] User authentication and persistence
- [ ] Multiple model selection
- [ ] File upload + RAG capabilities
- [ ] Conversation branching/forking
- [ ] Export conversations (PDF, Markdown)
- [ ] Custom system prompts
- [ ] Rate limiting per user
- [ ] Admin dashboard

## Troubleshooting

### Backend won't start
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check migrations
alembic current
alembic upgrade head

# Check logs
docker compose logs backend
```

### Frontend can't connect to backend
- Ensure backend is running: `curl http://localhost:8000/health`
- Check CORS headers in browser console
- Verify `X-Client-Id` header is being sent
- Check API client URL in `shared/api/client.ts`

### Messages not streaming
- Check browser DevTools > Network tab for SSE stream
- Verify OpenRouter API key is valid
- Check backend logs for LLM service errors

### Database errors
```bash
# Reset database (dev only!)
docker compose down -v
docker compose up

# Or manually:
alembic downgrade base  # Remove all migrations
alembic upgrade head    # Reapply from scratch
```

## Architecture Decisions

### Why Zustand + React Query?
- **Zustand**: Minimal, performant UI state for streaming/real-time updates
- **React Query**: Automatic cache management, refetch logic, offline support

### Why PostgreSQL instead of SQLite?
- Better support for async operations with asyncpg
- UUID type support out of the box
- Better for production deployments

### Why SSE instead of WebSockets?
- Simpler to implement and test
- Sufficient for one-way server→client streaming
- No connection state management needed

### Why Anonymous Users?
- Lower friction to use (no signup)
- Suitable for demo/prototype
- Easy to add auth layer later

## License

MIT (or as specified in project requirements)
