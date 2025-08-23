from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class Message(BaseModel):
    message_id: str
    created_at: Optional[datetime] = None
    phone_number: str
    thread_id: str
    content: str
    role: str



