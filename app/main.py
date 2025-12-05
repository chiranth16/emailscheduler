from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel
from datetime import datetime
import httpx
from typing import List
from uuid import uuid4

from app.mailer import fetch_weather, compose_email, send_email_console
from app.store import SCHEDULES, SEND_LOGS
from app.excel_reader import read_schedules
from app.scheduler import start_scheduler, stop_scheduler

app = FastAPI(title="email-scheduler-dev")

# ------------------------------------------------------
# Root + Health
# ------------------------------------------------------
@app.get("/")
async def root():
    return {"status": "ok", "message": "Email Scheduler service (dev)"}


class HealthResponse(BaseModel):
    status: str
    server_time: datetime


@app.get("/health", response_model=HealthResponse)
async def health():
    return {"status": "ok", "server_time": datetime.utcnow()}


# ------------------------------------------------------
# Weather
# ------------------------------------------------------
@app.get("/weather")
async def get_weather(
    latitude: float = Query(...),
    longitude: float = Query(...),
):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {"latitude": latitude, "longitude": longitude, "current_weather": "true"}

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Error fetching weather: {exc}")

    return data.get("current_weather", data)


# ------------------------------------------------------
# Schedule Models
# ------------------------------------------------------
class Schedule(BaseModel):
    id: str
    email: str
    date: str
    time: str
    timezone: str
    latitude: float
    longitude: float


class ScheduleCreate(BaseModel):
    email: str
    date: str
    time: str
    timezone: str
    latitude: float
    longitude: float


# ------------------------------------------------------
# Schedule API
# ------------------------------------------------------
@app.post("/schedules", response_model=Schedule)
async def create_schedule(payload: ScheduleCreate):
    """
    Create a schedule and store it in the shared in-memory list as a dict.
    """
    schedule = Schedule(id=str(uuid4()), **payload.dict())
    # store as dict so scheduler can use item["date"], etc.
    SCHEDULES.append(schedule.dict())
    return schedule


@app.get("/schedules", response_model=List[Schedule])
async def list_schedules():
    """
    Return all schedules (convert stored dicts back to Schedule models).
    """
    return [Schedule(**s) for s in SCHEDULES]


@app.get("/schedules/{schedule_id}", response_model=Schedule)
async def get_schedule(schedule_id: str):
    for s in SCHEDULES:
        if s["id"] == schedule_id:
            return Schedule(**s)
    raise HTTPException(status_code=404, detail="Schedule not found")


@app.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str):
    for s in list(SCHEDULES):
        if s["id"] == schedule_id:
            SCHEDULES.remove(s)
            return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Schedule not found")


# ------------------------------------------------------
# Import from Excel
# ------------------------------------------------------
class ExcelImportRequest(BaseModel):
    path: str


@app.post("/schedules/import-excel", response_model=List[Schedule])
async def import_schedules_from_excel(payload: ExcelImportRequest):
    """
    Read schedules from an Excel file and add them to SCHEDULES.
    """
    try:
        rows = read_schedules(payload.path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Excel file not found")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error reading Excel: {exc}")

    imported: List[Schedule] = []

    for row in rows:
        try:
            schedule = Schedule(
                id=str(uuid4()),
                email=row["email"],
                date=row["date"],
                time=row["time"],
                timezone=row["timezone"],
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
            )
            # store dict for scheduler
            SCHEDULES.append(schedule.dict())
            imported.append(schedule)
        except KeyError as missing:
            raise HTTPException(status_code=400, detail=f"Missing column: {missing}")

    return imported


# ------------------------------------------------------
# Send Test Email (Mock via Console)
# ------------------------------------------------------
class SendTestRequest(BaseModel):
    email: str
    latitude: float
    longitude: float


@app.post("/send-test-email")
async def send_test_email(payload: SendTestRequest = Body(...)):
    """
    Fetch weather for given coordinates, compose a mock email,
    and log it to the console instead of sending.
    """
    try:
        weather = await fetch_weather(payload.latitude, payload.longitude)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Weather fetch failed: {exc}")

    email_obj = compose_email(payload.email, weather)
    send_email_console(email_obj)

    return {
        "status": "mock-sent",
        "to": payload.email,
        "subject": email_obj["subject"],
    }


# ------------------------------------------------------
# Scheduler lifecycle hooks & send logs endpoint
# ------------------------------------------------------
@app.on_event("startup")
async def _startup_scheduler():
    # start scheduler after app starts
    start_scheduler()


@app.on_event("shutdown")
async def _shutdown_scheduler():
    stop_scheduler()


@app.get("/send-logs")
async def get_send_logs():
    """
    Return simple send logs recorded by the scheduler (mock sends).
    """
    return SEND_LOGS
