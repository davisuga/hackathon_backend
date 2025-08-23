from pydantic import BaseModel
from datetime import datetime

class Message(BaseModel):
    message_id: str
    created_at: datetime
    phone_number: str
    thread_id: str
    content: str
    role: str



