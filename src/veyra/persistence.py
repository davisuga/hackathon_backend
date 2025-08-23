from __future__ import annotations
import os
import asyncpg
from contextlib import asynccontextmanager
from typing import AsyncIterator, Any
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from src.whatsapp.model import Message
from .models import AutoMarketState, WorkflowStatus

DB_URL = os.getenv("POSTGRES_URL")
assert DB_URL, "POSTGRES_URL environment variable not set."

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

class PostgresStorage(Storage):
    """PostgreSQL implementation of the Storage interface."""
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def get_workflow(self, thread_id: str) -> AutoMarketState | None:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM workflows WHERE thread_id = $1", thread_id)
            return AutoMarketState(**dict(row)) if row else None

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
                state.thread_id, state.status, state.conversation_transcript
            )
        return state

    async def update_workflow(self, state: AutoMarketState) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE workflows SET
                    status = $2,
                    briefing_md = $3,
                    strategy_and_plan_md = $4,
                    image_urls = $5,
                    html_content = $6,
                    page_url = $7,
                    updated_at = NOW()
                WHERE thread_id = $1
                """,
                state.thread_id, state.status, state.briefing_md, state.strategy_and_plan_md,
                state.image_urls, state.html_content, state.page_url
            )

    async def get_page_content(self, thread_id: str) -> str | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchval("SELECT html_content FROM workflows WHERE thread_id = $1", thread_id)
        
    ## Messages

    async def insert_message(self, message: Message):
        async with self.pool.acquire() as conn:
             await conn.execute(
                """
                INSERT INTO messages (thread_id, message_id, role, content)
                VALUES ($1, $2, $3, $4)
                """,
                message.thread_id, message.message_id, message.role, message.content
            )
             
    ## End of Messages

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
                               
                CREATE TABLE IF NOT EXISTS messages (
                    message_id VARCHAR(32) PRIMARY KEY,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    thread_id VARCHAR(32) NOT NULL,
                    role VARCHAR(12) NOT NULL,
                    content TEXT
                );
            """) #TODO: Create index by thread id over messages tabl
        yield pool
    finally:
        await pool.close()