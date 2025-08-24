from __future__ import annotations
import os
import asyncpg
import json
from contextlib import asynccontextmanager
from typing import AsyncIterator, Any, List, Dict
from pydantic import TypeAdapter
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter


from .agents import CalendarPost

from src.whatsapp.model import Message

from .models import AutoMarketState, WorkflowStatus

DB_URL = os.getenv("POSTGRES_URL")
assert DB_URL, "POSTGRES_URL environment variable not set."


class WorkflowTransitionError(Exception):
    """Raised when an invalid workflow state transition is attempted."""

    pass


class Storage:
    """Abstract base class for a durable storage interface."""

    async def get_workflow(self, thread_id: str) -> AutoMarketState | None:
        raise NotImplementedError

    async def create_workflow(self, thread_id: str, transcript: str) -> AutoMarketState:
        raise NotImplementedError

    async def update_workflow(self, state: AutoMarketState) -> None:
        raise NotImplementedError

    async def get_page_content(self, thread_id: str) -> str | None:
        raise NotImplementedError

    async def insert_message(self, message: Message):
        raise NotImplementedError
    async def get_number_by_thread_id(
        self, thread_id:str
    )-> str:
        raise NotImplementedError

class PostgresStorage(Storage):
    """PostgreSQL implementation of the Storage interface."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    async def get_number_by_thread_id(self, thread_id:str)-> str:
        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT phone_number FROM messages WHERE thread_id = $1 limit 1", thread_id
            )
    async def get_workflow(self, thread_id: str) -> AutoMarketState | None:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM workflows WHERE thread_id = $1", thread_id
            )
            if not row:
                return None

            # Convert row to dict and handle JSONB calendar_events
            row_dict = dict(row)
            if row_dict.get("calendar_events"):
                # JSONB is already parsed by asyncpg
                row_dict["calendar_events"] = row_dict["calendar_events"]

            return AutoMarketState(**row_dict)

    async def create_workflow(self, thread_id: str, transcript: str) -> AutoMarketState:
        state = AutoMarketState(
            thread_id=thread_id,
            status=WorkflowStatus.STARTED,
            conversation_transcript=transcript,
        )
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO workflows (thread_id, status, conversation_transcript)
                VALUES ($1, $2, $3)
                """,
                state.thread_id,
                state.status,
                state.conversation_transcript,
            )
        return state

    async def update_workflow(self, state: AutoMarketState) -> None:
        events_ta = TypeAdapter(list[CalendarPost])
        async with self.pool.acquire() as conn:
            calendar_events_json = None
            if hasattr(state, "calendar_events") and state.calendar_events:
                calendar_events_json = events_ta.dump_json(
                    state.calendar_events
                ).decode("utf-8")

            await conn.execute(
                """
                UPDATE workflows SET
                    status = $2,
                    briefing_md = $3,
                    strategy_and_plan_md = $4,
                    calendar_events = $5::jsonb,
                    image_urls = $6,
                    html_content = $7,
                    page_url = $8,
                    updated_at = NOW()
                WHERE thread_id = $1
                """,
                state.thread_id,
                state.status,
                state.briefing_md,
                state.strategy_and_plan_md,
                calendar_events_json,
                state.image_urls,
                state.html_content,
                state.page_url,
            )

    async def get_page_content(self, thread_id: str) -> str | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT html_content FROM workflows WHERE thread_id = $1", thread_id
            )

    ## Messages

    async def insert_message(self, message: Message):
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO messages (phone_number, thread_id, message_id, role, content)
                VALUES ($1, $2, $3, $4, $5)
                """,
                message.phone_number,
                message.thread_id,
                message.message_id,
                message.role,
                message.content,
            )

    ## End of Messages
    ## Brands

    ## End of Brands

@asynccontextmanager
async def db_pool() -> AsyncIterator[asyncpg.Pool]:
    """Provides a connection pool to the PostgreSQL database."""
    pool = await asyncpg.create_pool(dsn=DB_URL)
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS workflows (
                    thread_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    conversation_transcript TEXT NOT NULL,
                    briefing_md TEXT,
                    strategy_and_plan_md TEXT,
                    image_urls TEXT[],
                    html_content TEXT,
                    page_url TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );
                ALTER TABLE workflows ADD COLUMN IF NOT EXISTS calendar_events JSONB;
            """)

            # Create index on calendar events for better query performance
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_workflows_calendar_events 
                ON workflows USING GIN (calendar_events);


                               
                CREATE TABLE IF NOT EXISTS messages (
                    message_id VARCHAR(32) PRIMARY KEY,
                    phone_number VARCHAR(16) NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    thread_id VARCHAR(48) NOT NULL,
                    role VARCHAR(12) NOT NULL,
                    content TEXT
                );
            """)  # TODO: Create index by thread id over messages tabl

            await conn.execute("""
              CREATE TABLE IF NOT EXISTS brands (
                    brand_id SERIAL PRIMARY KEY,
                    brand_name VARCHAR(48) NOT NULL,
                    user_phone VARCHAR(16) NOT NULL,
                    main_color VARCHAR(8) NOT NULL
                );    
                """)

        yield pool
    finally:
        await pool.close()
