# backend/app/main.py
from fastapi import FastAPI
from .api import router as api_router
from .api_endpoints import router as api_endpoints_router

app = FastAPI(title="Monitoring API")

app.include_router(api_router, prefix="/api")
app.include_router(api_endpoints_router, prefix="/api")
