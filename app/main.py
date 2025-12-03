from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(title="email-scheduler-dev")

@app.get("/")
async def root():
    return {"status": "ok", "message": "Email Scheduler service (dev)"}

class HealthResponse(BaseModel):
    status: str
    server_time: datetime

@app.get("/health", response_model=HealthResponse)
async def health():
    return {"status": "ok", "server_time": datetime.utcnow()}
