from contextlib import asynccontextmanager
from typing import Optional
from dotenv.main import load_dotenv
from fastapi.responses import JSONResponse

from src.utils import color_a_hex
load_dotenv()


from src.veyra.img_gen import upload_to_s3

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


async def save_logo(agent: Agent) -> Optional[str]:
    """
    This tools allows the agent to store the logo image, no parameters are required since
    the image is already in the context.
    """
    image = agent.session_state.get("__image_path", None)
    if not image:
        return None
    file_path = await upload_to_s3(image)
    return file_path

def upsert_brand_info(brand_name: str, user_name: str, brand_color: str, agent: Agent):
    """
    Updates the current user's brand info with the provided information. This took should be
    invoked after the user have saved their logo, please don't call this tool before

    :param str brand_name: the brand's name
    :param str user_name: the user's name
    :param str brand_color: uno de los colores conocidos negro, blanco, 
    gris, rojo, rosa, purpura, violeta, indigo,
    azul, celeste, cian, teal, verde, verde_claro, lima, amarillo,
    ambar, naranja, naranja_profundo, cafe, azul_grisaceo.
    """
    print("Saving brand's info")



media_agent = Agent(
    name="Vero",
    
    instructions=instructions,
    add_name_to_instructions=True,

    goal=goal,

    # model=Gemini(id="gemini-2.0-flash"),
    model=OpenAIChat(),
    tools=[generate_call_link, save_logo, color_a_hex],
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

@app.exception_handler(Exception)
async def validation_exception_handler(request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": str(exc)},
    )

if __name__ == "__main__":
    whatsapp_app.serve(app="main:app", port=8000, reload=True)
