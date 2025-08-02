from fastapi import APIRouter
from app.api.v1.endpoints import runs

api_router = APIRouter()
api_router.include_router(
    runs.router, 
    prefix="/run", 
    tags=["Company Analysis", "Data Export", "Budget Management"],
    responses={404: {"description": "Not found"}}
)