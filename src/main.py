import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from routers import api_router

app = FastAPI()

app.include_router(api_router)


@app.get("/")
async def docs_redirect():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
