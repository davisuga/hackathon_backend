import os
from contextlib import asynccontextmanager
from typing import Any

import logfire
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from pydantic_ai.ag_ui import handle_ag_ui_request

from .models import RunRequestBody
from .persistence import PostgresStorage, db_pool
from .tools import orchestrator_agent, RunDependencies

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
async def health_check():
    return {"status": "ok"}

@app.post("/")
async def run_automarket_agent(body: RunRequestBody, request: Request) -> Response:
    """Main AG-UI endpoint."""
    storage: PostgresStorage = request.state.storage
    thread_id = body.thread_id or "default"

    workflow = await storage.get_workflow(thread_id)
    if not workflow:
        if not body.messages or not body.messages[0].parts:
            return Response("Initial message is empty", status_code=400)
        first_message = body.messages[0].parts[0].text
        workflow = await storage.create_workflow(thread_id, first_message)
    
    # Create dependencies for this specific run
    run_deps = RunDependencies(thread_id=thread_id, storage=storage)

    return await handle_ag_ui_request(
        agent=orchestrator_agent,
        request=request,
        deps=run_deps,
    )

@app.get("/pages/{thread_id}", response_class=HTMLResponse)
async def get_landing_page(thread_id: str, request: Request):
    """Serves the generated HTML landing page from the database."""
    storage: PostgresStorage = request.state.storage
    html_content = await storage.get_page_content(thread_id)
    if html_content is None:
        return HTMLResponse(content="<h1>Page Not Found or Not Yet Generated</h1>", status_code=404)
    return HTMLResponse(content=html_content)

@app.get("/", response_class=HTMLResponse)
async def root():
    """Simple landing page with instructions."""
    return """
    <html>
        <head><title>AutoMarket Agent</title></head>
        <body>
            <h1>AutoMarket Agent is running</h1>
            <p>
                Connect to this endpoint (<code>http://localhost:8000</code>)
                from the <a href="http://localhost:3000" target="_blank">AG-UI Dojo</a>.
            </p>
        </body>
    </html>
    """