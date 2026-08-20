from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.app.db.client import client

@asynccontextmanager
async def lifespan(app: FastAPI):
    await client.admin.command("ping")
    yield
    await client.close()

app = FastAPI()

@app.get("/")
def root():
    return {"message":"API is running for the FastAPI application."}