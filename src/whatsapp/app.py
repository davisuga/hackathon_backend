from typing import Awaitable, Callable
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter

from agno.app.base import BaseAPIApp
from src.whatsapp.async_router import get_async_router
from src.whatsapp.sync_router import get_sync_router
from starlette.middleware.cors import CORSMiddleware


class WhatsappAPI(BaseAPIApp):
    type = "whatsapp"

    def __init__(self, session_state_loader: Callable[[str], Awaitable[dict]] = None, **kwargs):
        super().__init__(**kwargs)
        self.session_state_loader = session_state_loader

    def get_router(self) -> APIRouter:
        return get_sync_router(agent=self.agent, team=self.team)

    def get_async_router(self) -> APIRouter:
        return get_async_router(agent=self.agent, team=self.team, session_state_loader=self.session_state_loader)
    
    def get_app(self, use_async: bool = True, prefix: str = "", lifespan = None) -> FastAPI:
        if not self.api_app:
            kwargs = {
                "title": self.settings.title,
            }
            if self.version:
                kwargs["version"] = self.version
            if self.settings.docs_enabled:
                kwargs["docs_url"] = "/docs"
                kwargs["redoc_url"] = "/redoc"
                kwargs["openapi_url"] = "/openapi.json"

            self.api_app = FastAPI(
                **kwargs,  # type: ignore
                lifespan=lifespan
            )

        if not self.api_app:
            raise Exception("API App could not be created.")

        @self.api_app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": str(exc.detail)},
            )

        async def general_exception_handler(request: Request, call_next):
            try:
                return await call_next(request)
            except Exception as e:
                return JSONResponse(
                    status_code=e.status_code if hasattr(e, "status_code") else 500,
                    content={"detail": str(e)},
                )

        self.api_app.middleware("http")(general_exception_handler)

        if not self.router:
            self.router = APIRouter(prefix=prefix)

        if not self.router:
            raise Exception("API Router could not be created.")

        if use_async:
            self.router.include_router(self.get_async_router())
        else:
            self.router.include_router(self.get_router())

        self.api_app.include_router(self.router)

        self.api_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
             allow_credentials=False,
            allow_headers=["*"],
            expose_headers=["*"],
        )

        return self.api_app
