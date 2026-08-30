"""FastAPI endpoints"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .core.store import store
from .core.models import Commitment, CommitmentStatus, Source
from .modes.one_thing import one_thing
from .modes.gather import gather
from .modes.reduce import reduce_mode
from .modes.conversation import conversation
from .modes.just_in_time import just_in_time
from .modes.executor import executor
from .cron.scheduler import CronScheduler
from .cron import jobs as cron_jobs

scheduler = CronScheduler()
scheduler.register("gather", cron_jobs.gather_all)
scheduler.register("reduce", cron_jobs.reduce_all)
scheduler.register("expire", cron_jobs.expire_old)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown"""
    # Initialize database
    try:
        await store.init_db()
    except Exception as e:
        print(f"DB init error: {e}")
    
    scheduler.run_in_background()
    yield


app = FastAPI(
    title="Order",
    description="Agentic Life Order System",
    version="0.1.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== ONE-THING MODE ==============

@app.get("/api/one-thing")
async def get_one_thing():
    """Get the ONE thing to focus on"""
    thing = await one_thing.get_one_thing()
    if not thing:
        return {"status": "empty", "message": "No pending commitments"}
    return thing.model_dump()


class ActionRequest(BaseModel):
    commitment_id: str


@app.post("/api/one-thing/done")
async def mark_done(req: ActionRequest):
    """Mark commitment as done"""
    await one_thing.mark_done(req.commitment_id)
    return {"status": "done"}


@app.post("/api/one-thing/skip")
async def skip(req: ActionRequest):
    """Skip commitment"""
    await one_thing.skip(req.commitment_id)
    return {"status": "skipped"}


@app.get("/api/one-thing/why")
async def explain_why(commitment_id: str):
    """Explain why this was chosen"""
    all = await store.get_all()
    commitment = next((c for c in all if c.id == commitment_id), None)
    if not commitment:
        raise HTTPException(404, "Commitment not found")
    explanation = await one_thing.explain(commitment)
    return {"explanation": explanation}


# ============== GATHER MODE ==============

@app.get("/api/gather")
async def gather_all_sources():
    """Gather from all sources"""
    results = await gather.gather_all()
    return {
        "status": "done",
        "results": [r.model_dump() for r in results]
    }


@app.get("/api/gather/test")
async def test_connections():
    """Test all connections"""
    return await gather.test_connections()


# ============== REDUCE MODE ==============

@app.get("/api/reduce")
async def reduce_commitments():
    """Filter and prioritize commitments"""
    result = await reduce_mode.reduce()
    return result.model_dump()


@app.get("/api/stats")
async def get_stats():
    """Get current statistics"""
    counts = await store.count_by_status()
    return {
        "pending": counts.get("pending", 0),
        "done": counts.get("done", 0),
        "ignored": counts.get("ignored", 0),
        "expired": counts.get("expired", 0)
    }


# ============== CONVERSATION MODE ==============

class ChatRequest(BaseModel):
    message: str


@app.post("/api/chat")
async def chat(req: ChatRequest):
    """Conversation mode"""
    response = await conversation.chat(req.message)
    return {"response": response}


@app.post("/api/chat/reset")
async def reset_chat():
    """Reset conversation"""
    conversation.reset()
    return {"status": "reset"}


# ============== JUST-IN-TIME MODE ==============

class SearchRequest(BaseModel):
    query: str


@app.post("/api/search")
async def search_commitments(req: SearchRequest):
    """Search commitments"""
    results = await just_in_time.search(req.query)
    return {"results": [r.model_dump() for r in results]}


@app.get("/api/promises")
async def what_did_i_promise(timeframe: str = "this week"):
    """What did I promise?"""
    results = await just_in_time.what_did_i_promise(timeframe)
    return {"results": [r.model_dump() for r in results]}


@app.get("/api/about")
async def what_about(topic: str):
    """What about X?"""
    results = await just_in_time.what_about_x(topic)
    return {"results": [r.model_dump() for r in results]}


# ============== EXECUTOR MODE ==============

@app.get("/api/commitments")
async def list_commitments():
    """List all commitments"""
    all = await store.get_all()
    return {"commitments": [c.model_dump() for c in all]}


@app.get("/api/commitments/{commitment_id}")
async def get_commitment(commitment_id: str):
    """Get specific commitment"""
    all = await store.get_all()
    commitment = next((c for c in all if c.id == commitment_id), None)
    if not commitment:
        raise HTTPException(404, "Commitment not found")
    return commitment.model_dump()


@app.post("/api/commitments/{commitment_id}/action")
async def propose_action(commitment_id: str):
    """Propose action for commitment"""
    all = await store.get_all()
    commitment = next((c for c in all if c.id == commitment_id), None)
    if not commitment:
        raise HTTPException(404, "Commitment not found")
    action = await executor.propose_action(commitment)
    return action


@app.post("/api/commitments/{commitment_id}/execute")
async def execute_action(commitment_id: str, action: str):
    """Execute action on commitment"""
    commitment = await executor.commit(commitment_id, action)
    return commitment.model_dump()


# ============== CRON ==============

@app.get("/api/cron/status")
async def cron_status():
    """Get last-run timestamps for all cron jobs"""
    return scheduler.get_status()


@app.post("/api/cron/trigger/{job_name}")
async def trigger_job(job_name: str):
    """Manually trigger a cron job (gather | reduce | expire)"""
    if job_name not in ("gather", "reduce", "expire"):
        raise HTTPException(400, f"Unknown job: {job_name}. Use gather, reduce, or expire.")
    ran = await scheduler.run_job_now(job_name)
    if not ran:
        raise HTTPException(404, f"Job '{job_name}' not registered")
    return {"status": "triggered", "job": job_name}


# ============== HEALTH ==============

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {
        "name": "Order",
        "version": "0.1.0",
        "description": "Agentic Life Order System"
    }
