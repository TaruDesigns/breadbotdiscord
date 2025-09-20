from fastapi import APIRouter
from pydantic import BaseModel

from settings import SETTINGS

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}


class UpdateSettingsRequest(BaseModel):
    FILTER_BREAD_LABEL_CONFIDENCE: float | None = None
    FILTER_BREAD_SEG_CONFIDENCE: float | None = None
    BREAD_DETECTION_CONFIDENCE: float | None = None
    OVERRIDE_DETECTION_CONFIDENCE: float | None = None


@router.post("/update-settings")
async def set_infer_confidence(req: UpdateSettingsRequest):
    SETTINGS.filter_bread_label_confidence = (
        req.FILTER_BREAD_LABEL_CONFIDENCE
        if req.FILTER_BREAD_LABEL_CONFIDENCE is not None
        else SETTINGS.filter_bread_label_confidence
    )
    SETTINGS.filter_bread_seg_confidence = (
        req.FILTER_BREAD_SEG_CONFIDENCE
        if req.FILTER_BREAD_SEG_CONFIDENCE is not None
        else SETTINGS.filter_bread_seg_confidence
    )
    SETTINGS.bread_detection_confidence = (
        req.BREAD_DETECTION_CONFIDENCE
        if req.BREAD_DETECTION_CONFIDENCE is not None
        else SETTINGS.bread_detection_confidence
    )
    SETTINGS.override_detection_confidence = (
        req.OVERRIDE_DETECTION_CONFIDENCE
        if req.OVERRIDE_DETECTION_CONFIDENCE is not None
        else SETTINGS.override_detection_confidence
    )
    return
