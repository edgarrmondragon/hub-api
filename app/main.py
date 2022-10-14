"""Hub API."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.api_v1.api import router as api_router

app = FastAPI()


app.include_router(api_router, prefix="/meltano/api/v1")
app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")
