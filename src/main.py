from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from loguru import logger

from registry import REGISTRY
from routers import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    REGISTRY.db.create_db()
    await REGISTRY.bot.start(REGISTRY.settings.discord_token)
    yield
    logger.info("Shutting down...")


app = FastAPI()

app.include_router(api_router)


@app.get("/")
async def docs_redirect():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
