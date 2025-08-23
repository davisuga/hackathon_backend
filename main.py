from contextlib import asynccontextmanager
from dotenv.main import load_dotenv
from fastapi import FastAPI

from src.veyra.persistence import db_pool
load_dotenv()

import os
from agno.agent import Agent

from src.whatsapp import WhatsappAPI
from agno.models.openai import OpenAIChat
import logging

from agno.memory.v2 import Memory
from agno.storage.postgres import PostgresStorage
from agno.memory.v2.db.postgres import PostgresMemoryDb
from src.marketing.instructions import instructions

from langfuse import get_client, observe
import openlit

langfuse = get_client()
openlit.init(tracer=langfuse._otel_tracer, disable_batch=True, application_name="zeropipol")

db_url = os.environ['POSTGRES_URL']

logger = logging.getLogger(__name__)


media_agent = Agent(
    name="Andri",
    
    instructions=instructions,
    add_name_to_instructions=True,

    model=OpenAIChat(id="gpt-4o"),
    tools=[],
    show_tool_calls=True,
    enable_session_summaries=True,

    add_datetime_to_instructions=True,
    add_state_in_messages=True,

    enable_agentic_memory=True,
    # add_location_to_instructions=True,
    add_history_to_messages=True,
    num_history_responses=20,
    num_history_runs=5,
    storage=PostgresStorage(
        table_name="agent_sessions", db_url=db_url, schema="public"
    ),
    memory=Memory(
        db=PostgresMemoryDb(
            table_name="agent_memories",
            db_url=db_url, 
            schema="public"
        )
    ),
    markdown=True
)

async def build_context(phone:  str) -> dict:
    return {}


whatsapp_app = WhatsappAPI(
    agent=media_agent,
    name="Zeropipol",
    app_id="zeropipol_agent",
    description="Un agente de marketing que puede almacenar",
    session_state_loader=build_context
)

app = whatsapp_app.get_app()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the database connection pool during the app's lifecycle."""
    async with db_pool() as pool:
        storage = PostgresStorage(pool)
        # logfire.instrument_fastapi(app)
        yield {"storage": storage}

if __name__ == "__main__":
    whatsapp_app.serve(app="main:app", port=8000, reload=True, lifespan="on")
