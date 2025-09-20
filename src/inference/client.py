import httpx
from loguru import logger
from pydantic import BaseModel


class ImageData(BaseModel):
    image: str  # base64 encoded image


class PredictResponse(BaseModel):
    image: str | None  # base64 encoded image
    roundness: float | None
    labels: dict[str, float] | None  # Labels with confidences


class PredictionError(Exception): ...


class InferenceClient:
    def __init__(self, base_url: str):
        self.client = lambda: httpx.AsyncClient(base_url=base_url)

    async def predict(self, payload: ImageData) -> PredictResponse:
        async with self.client() as client:
            res = await client.post("/predict/predict", json=payload.model_dump())
            if res.status_code != 200:
                raise PredictionError()
            return PredictResponse.model_validate(res.json())
