from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import traceback

from app.store import SCHEDULES, SEND_LOGS
from app.mailer import fetch_weather, compose_email, send_email_console

scheduler = AsyncIOScheduler()


async def _process_schedule_item(item: dict) -> bool:
    """
    Process a single schedule dict:
      - Build its local datetime from date+time+timezone
      - Convert to UTC and compare with now
      - If due, fetch weather, compose and mock-send email,
        append to SEND_LOGS, and return True
    """
    try:
        # Build local datetime from strings
        dt_str = f"{item['date']}T{item['time']}"  # e.g. "2025-12-05T13:45"
        local_dt = datetime.fromisoformat(dt_str)  # naive
        tz = ZoneInfo(item["timezone"])
        local_dt = local_dt.replace(tzinfo=tz)

        # Convert to UTC and compare
        utc_dt = local_dt.astimezone(timezone.utc)
        now_utc = datetime.now(timezone.utc)

        # Not yet time → skip
        if utc_dt > now_utc:
            return False

        # Time reached → send
        weather = await fetch_weather(item["latitude"], item["longitude"])
        email_obj = compose_email(item["email"], weather)
        send_email_console(email_obj)

        # Record in logs
        SEND_LOGS.append(
            {
                "schedule_id": item["id"],
                "email": item["email"],
                "sent_at": datetime.now(timezone.utc).isoformat(),
                "subject": email_obj["subject"],
                "weather_snapshot": weather,
            }
        )

        return True

    except Exception as e:
        print("Error processing schedule:", e)
        traceback.print_exc()
        return False


async def check_and_send():
    """
    Check all schedules and send any that are due.
    """
    items = list(SCHEDULES)
    if not items:
        return

    to_remove = []

    for item in items:
        try:
            sent = await _process_schedule_item(item)
            if sent:
                to_remove.append(item)
        except Exception:
            traceback.print_exc()

    # Remove sent items from SCHEDULES
    for item in to_remove:
        try:
            SCHEDULES.remove(item)
        except ValueError:
            # In case it was already removed
            pass


def start_scheduler():
    """
    Start APScheduler with a job that runs every 30 seconds.
    """
    if not scheduler.get_jobs():
        scheduler.add_job(
            check_and_send,
            IntervalTrigger(seconds=30),
            id="check_and_send",
        )
    scheduler.start()
    print("APScheduler started (checking schedules every 30 seconds)")


def stop_scheduler():
    """
    Stop the scheduler on app shutdown.
    """
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("APScheduler stopped")
