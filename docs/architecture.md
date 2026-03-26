# Architecture

## System Overview

Order is an agentic life order system that gathers scattered commitments from multiple sources and surfaces them through different interaction modes.

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│                    (Next.js + Tailwind)                      │
│   ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐     │
│   │Drown │ │Scatt │ │Stuck │ │Accum │ │Spec  │ │Ready │     │
│   └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘     │
│      │        │        │        │        │        │          │
│   ┌──┴────────┴────────┴────────┴────────┴────────┴───┐     │
│   │              Mode Selector                         │     │
│   └────────────────────┬──────────────────────────────┘     │
└────────────────────────┼─────────────────────────────────────┘
                         │ HTTP/SSE
┌────────────────────────┼─────────────────────────────────────┐
│                        │ Backend                             │
│                        ▼                                     │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                   FastAPI                            │   │
│   │  /api/one-thing  /api/gather  /api/chat  ...       │   │
│   └────────────────────┬────────────────────────────────┘   │
│                        │                                     │
│   ┌────────────────────┼────────────────────────────────┐   │
│   │                    ▼                                 │   │
│   │   ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│   │   │  Modes   │  │ Synthesis│  │   Cron   │          │   │
│   │   │  (6)     │  │  (LLM)   │  │ Scheduler│          │   │
│   │   └────┬─────┘  └────┬─────┘  └────┬─────┘          │   │
│   │        │             │             │                 │   │
│   │        └─────────────┼─────────────┘                 │   │
│   │                      ▼                               │   │
│   │            ┌──────────────────┐                      │   │
│   │            │  SQLite Store    │                      │   │
│   │            │  (async)         │                      │   │
│   │            └──────────────────┘                      │   │
│   └──────────────────────────────────────────────────────┘   │
│                        │                                     │
│   ┌────────────────────┼────────────────────────────────┐   │
│   │                    ▼      Gatherers                   │   │
│   │   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │   │
│   │   │ Discord │ │ GitHub  │ │    X    │ │  Gmail  │   │   │
│   │   │TinyFish │ │API      │ │TinyFish │ │TinyFish │   │   │
│   │   └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘   │   │
│   └────────┼───────────┼───────────┼───────────┼─────────┘   │
└────────────┼───────────┼───────────┼───────────┼─────────────┘
             │           │           │           │
         ┌───┴───┐   ┌───┴───┐   ┌───┴───┐   ┌───┴───┐
         │Discord│   │GitHub │   │   X   │   │ Gmail │
         └───────┘   └───────┘   └───────┘   └───────┘
```

## Core Components

### 1. Gatherers
Collect commitments from external sources.

| Source | Method | When |
|--------|--------|------|
| Discord | TinyFish SSE | No API for message search |
| GitHub | REST API | Issues assigned, PRs awaiting review |
| X (Twitter) | TinyFish SSE | DMs, bookmarks |
| Gmail | TinyFish SSE | Actionable emails |

**Base Pattern**:
```python
class BaseGatherer(ABC):
    @abstractmethod
    async def gather(self) -> AsyncIterator[Commitment]: ...
    
    async def run(self) -> GatherResult:
        # Collect all commitments, return result
```

### 2. SQLite Store
Async persistence with SQLAlchemy ORM.

```python
class CommitmentRow(Base):
    id: str              # UUID
    source: str          # discord, github, x_dm, x_bookmark, gmail
    text: str            # Original message
    extracted_task: str  # AI-extracted task
    deadline: datetime   # Optional
    priority: int        # 0-3
    status: str          # pending, done, ignored, expired
    raw_data: JSON       # Full original data
```

### 3. AI Synthesis
LiteLLM-based filtering and prioritization.

```python
async def extract_commitment(text, source) -> dict
async def filter_commitments(commitments) -> List[Commitment]
async def prioritize_commitments(commitments) -> List[Commitment]
async def pick_one_thing(commitments) -> Commitment
```

**Fallback**: Works without LLM API key (simple priority sorting).

### 4. Cron Scheduler
Hermes-style file-based scheduler with tick pattern.

```python
class CronScheduler:
    def register(name, job_func)
    def run_in_background()
    # Uses fcntl for file locking
    # Tick every 60 seconds
```

**Jobs**:
- `gather_all` (every 5 min)
- `reduce_all` (every 10 min)
- `expire_old` (every hour)

### 5. Modes
Six interaction modes for different mental states.

| Mode | State | Behavior |
|------|-------|----------|
| One-Thing | Drowning | Show only ONE commitment |
| Gather | Scattered | Pull from all sources |
| Reduce | Accumulated | Filter noise, keep what matters |
| Conversation | Stuck | Thinking partner chat |
| Just-in-Time | Specific | Ask and receive, no storage |
| Executor | Ready | Agents handle tasks |

## Data Flow

```
1. User connects accounts (Discord, GitHub, X, Gmail)
2. Cron jobs gather commitments periodically
3. AI synthesis filters and prioritizes
4. Modes surface based on user's state
5. User acts (done, skip, delegate)
6. Status updates reflect in stats
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16, Tailwind, Bun |
| Backend | FastAPI, uvicorn |
| Storage | SQLite (async) + SQLAlchemy |
| AI | LiteLLM (any provider) |
| Scraping | TinyFish (authenticated browser) |
| Cron | Hermes-style file-based |
| Runtime | Python 3.13, uv |

## Key Design Decisions

### Why TinyFish?
Discord and X have no APIs for message search. TinyFish provides authenticated browser automation via SSE streaming.

### Why SQLite?
Simple, async, no server needed. Perfect for personal tool.

### Why 6 Modes?
Different chaos states need different interactions. One-size-fits-all doesn't work.

### Why Fallback Mode?
Production should work without LLM. Simple priority sorting is better than nothing.

## File Structure

```
order/
├── src/order/
│   ├── core/           # Models, config, store
│   ├── gatherers/      # TinyFish + API gatherers
│   ├── synthesis/      # LLM integration
│   ├── modes/          # 6 interaction modes
│   ├── cron/           # Background jobs
│   └── api.py          # FastAPI endpoints
│
└── frontend/
    ├── app/            # Next.js pages
    ├── components/     # Mode views
    └── lib/            # API client
```

## Security Considerations

- API keys stored in environment variables
- No user data stored permanently (commitments expire)
- TinyFish handles authentication (no credentials stored)
- Fallback mode works without external APIs
