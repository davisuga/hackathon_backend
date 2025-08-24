from contextlib import asynccontextmanager
from dotenv.main import load_dotenv
load_dotenv()

from fastapi import FastAPI
from src.veyra.persistence import db_pool
import os
from agno.agent import Agent

from src.whatsapp import WhatsappAPI
from agno.models.openai import OpenAIChat
from agno.models.google import Gemini
import logging

from agno.memory.v2 import Memory
from agno.storage.postgres import PostgresStorage
from agno.memory.v2.db.postgres import PostgresMemoryDb
from src.marketing.instructions import instructions, goal

from src.veyra.persistence import PostgresStorage as VeyraPostgresStorage

from langfuse import get_client, observe
import openlit

langfuse = get_client()
openlit.init(tracer=langfuse._otel_tracer, disable_batch=True, application_name="zeropipol")

db_url = os.environ['POSTGRES_URL']

logger = logging.getLogger(__name__)

def generate_call_link(agent: Agent):
    """
    This tool generates a link after the user's setup.
    """
    user_id = agent.user_id
    return f"https://prueba.com/{user_id}"


def save_logo(agent: Agent) -> bool:
    """
    This tools allows the agent to store the logo image, no parameters are required since
    the image is already in the context.
    """
    image = agent.session_state.get("__image_path", None)
    if not image:
        return False
    return True


media_agent = Agent(
    name="Vero",
    
    instructions=instructions,
    add_name_to_instructions=True,

    goal=goal,

    model=Gemini(id="gemini-2.0-flash"),
    tools=[generate_call_link, save_logo],
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
    name="Vero",
    app_id="zeropipol_agent",
    description="Un agente de marketing que puede almacenar",
    session_state_loader=build_context
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the database connection pool during the app's lifecycle."""
    async with db_pool() as pool:
        storage = VeyraPostgresStorage(pool)
        app.state.storage = storage
        yield {"storage": storage}

app = whatsapp_app.get_app(lifespan=lifespan)

if __name__ == "__main__":
    whatsapp_app.serve(app="main:app", port=8000, reload=True)
