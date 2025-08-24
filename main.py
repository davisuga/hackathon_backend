from contextlib import asynccontextmanager
from typing import Optional
import asyncpg
from dotenv.main import load_dotenv
from fastapi.responses import JSONResponse
from pathlib import Path

from src.utils import color_a_hex
load_dotenv()

from src.whatsapp.model import Brand



from src.veyra.img_gen import upload_to_s3

from fastapi import FastAPI
from src.veyra.persistence import Storage, db_pool
import os
from agno.agent import Agent

from src.whatsapp.app import WhatsappAPI
from agno.models.openai import OpenAIChat
import logging

from agno.memory.v2 import Memory
from agno.storage.postgres import PostgresStorage
from agno.memory.v2.db.postgres import PostgresMemoryDb
from src.marketing.instructions import instructions

from src.veyra.persistence import PostgresStorage as VeyraPostgresStorage

from langfuse import get_client
from src.veyra.workflow import renderer
import openlit

logger = logging.getLogger(__name__)
langfuse = get_client()
agent_storage = None
openlit.init(tracer=langfuse._otel_tracer, disable_batch=True, application_name="zeropipol")

db_url = os.environ['POSTGRES_URL']

logger = logging.getLogger(__name__)

async def get_storage() -> Storage:
    global agent_storage
    if agent_storage is None:
        pool = await asyncpg.create_pool(dsn=db_url, statement_cache_size=0,  # <- clave
        max_cached_statement_lifetime=0,  # opcional, aún más seguro
        max_cacheable_statement_size=0,)
        agent_storage = VeyraPostgresStorage(pool)
    return agent_storage

async def generate_call_link(agent: Agent):
    """
    This tool generates a link after the user's setup.
    """
    user_id = agent.user_id
    return f"https://veyra-frontend.vercel.app/?userId={user_id}"


async def save_logo(input, agent: Agent) -> Optional[str]:
    """
    This tools allows the agent to store the logo image, no parameters are required since
    the image is already in the context.
    """
    image = agent.session_state.get("__image_path", None)
    if not image:
        return None
    
    path = Path(image)
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo {file_path}")

    # Leer bytes
    with open(path, "rb") as f:
        data = f.read()
        file_path = await upload_to_s3(data)
        return file_path

async def upsert_brand_info_tool(brand_name: str, user_name: str, brand_color: str, logo_url: str, agent: Agent):
    """
    Updates the current user's brand info with the provided information. This took should be
    invoked after the user have saved their logo, please don't call this tool before

    :param str brand_name: the brand's name
    :param str user_name: the user's name
    :param str brand_color: uno de los colores conocidos negro, blanco, 
    gris, rojo, rosa, purpura, violeta, indigo,
    azul, celeste, cian, teal, verde, verde_claro, lima, amarillo,
    ambar, naranja, naranja_profundo, cafe, azul_grisaceo.
    :param str logo_url: the public's logo url
    """
    user_phone = agent.user_id
    brand = Brand(brand_name=brand_name, user_name=user_name, user_phone=user_phone, main_color=brand_color, brand_logo=logo_url)
    storage = await get_storage()
    await storage.upsert_brand(brand)
    print(brand)



media_agent = Agent(
    name="Vero",
    
    instructions=instructions,
    add_name_to_instructions=True,

    # model=Gemini(id="gemini-2.0-flash"),
    model=OpenAIChat(),
    tools=[generate_call_link, save_logo, color_a_hex, upsert_brand_info_tool],
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
        renderer.stop()
        

app = whatsapp_app.get_app(lifespan=lifespan)

@app.exception_handler(Exception)
async def validation_exception_handler(request, exc: Exception):
    logger.error(f"Uncaught error {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": str(exc)},
    )

if __name__ == "__main__":
    whatsapp_app.serve(app="main:app", port=8000, reload=True, host="0.0.0.0")

