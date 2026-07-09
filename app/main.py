from fastapi import FastAPI

from app.api import health, movies

app = FastAPI()

app.include_router(health.router)
app.include_router(movies.router)
