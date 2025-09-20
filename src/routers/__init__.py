from fastapi import APIRouter

from .admin import router as admin_router

api_router = APIRouter()
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
