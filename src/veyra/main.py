import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
import logfire
from dotenv import load_dotenv



from .workflow import run_generation_flow

from .persistence import PostgresStorage, db_pool

# Load environment variables and configure logging
load_dotenv()
logfire.configure(token=os.getenv("LOGFIRE_API_TOKEN"))
logfire.instrument_httpx()
logfire.instrument_asyncpg()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the database connection pool during the app's lifecycle."""
    async with db_pool() as pool:
        storage = PostgresStorage(pool)
        logfire.instrument_fastapi(app)
        yield {"storage": storage}


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health_check(request: Request):
    return {"status": "ok"}


@app.post("/")
async def run_automarket_agent(request: Request) -> None:
    """Main AG-UI endpoint."""
    storage: PostgresStorage = request.state.storage

    # Let handle_ag_ui_request parse the body. We parse it here first
    # to get the thread_id and initialize the workflow state.
    body = await request.json()
    thread_id = body.get("thread_id", "default")
    logfire.info("Received request for thread {thread_id}", thread_id=thread_id)
    
    await run_generation_flow(thread_id, storage)

