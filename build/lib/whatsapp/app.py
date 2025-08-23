from typing import Awaitable, Callable
from fastapi.routing import APIRouter

from agno.app.base import BaseAPIApp
from src.whatsapp.async_router import get_async_router
from src.whatsapp.sync_router import get_sync_router


class WhatsappAPI(BaseAPIApp):
    type = "whatsapp"

    def __init__(self, session_state_loader: Callable[[str], Awaitable[dict]] = None, **kwargs):
        super().__init__(**kwargs)
        self.session_state_loader = session_state_loader

    def get_router(self) -> APIRouter:
        return get_sync_router(agent=self.agent, team=self.team)

    def get_async_router(self) -> APIRouter:
        return get_async_router(agent=self.agent, team=self.team, session_state_loader=self.session_state_loader)
