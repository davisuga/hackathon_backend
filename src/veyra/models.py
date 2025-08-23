from __future__ import annotations
from dataclasses import dataclass, field

from enum import StrEnum
from pydantic import BaseModel
from typing import Any, List, Optional
from datetime import datetime
class CalendarPost(BaseModel):
    date: datetime
    title: str
    description: str

class WorkflowStatus(StrEnum):
    """Represents the current stage of the landing page generation workflow."""
    STARTED = "started"
    BRIEFING_COMPLETE = "briefing_complete"
    STRATEGY_COMPLETE = "strategy_complete"
    CALENDAR_COMPLETE = "calendar_complete"
    IMAGES_COMPLETE = "images_complete"
    HTML_COMPLETE = "html_complete"
    PUBLISHED = "published"
    FAILED = "failed"

@dataclass
class AutoMarketState:
    """In-memory representation of the workflow state for a given thread."""
    thread_id: str
    status: WorkflowStatus
    conversation_transcript: str
    briefing_md: str | None = None
    strategy_and_plan_md: str | None = None
    image_urls: list[str] = field(default_factory=list)
    html_content: str | None = None
    page_url: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    calendar_events: list[CalendarPost] | None = None


class MessagePart(BaseModel):
    text: str


class Message(BaseModel):
    parts: List[MessagePart]


class RunRequestBody(BaseModel):
    thread_id: Optional[str] = None
    messages: List[Message]
