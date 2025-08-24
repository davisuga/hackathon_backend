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


class Brand(BaseModel):
    brand_name: str
    user_phone: str
    user_name: str
    brand_logo: str
    main_color: str