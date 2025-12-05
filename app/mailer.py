import httpx
from typing import Dict, Any

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

async def fetch_weather(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Fetch current weather from Open-Meteo and return the 'current_weather' block.
    """
    params = {"latitude": latitude, "longitude": longitude, "current_weather": "true"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(OPEN_METEO_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
    return data.get("current_weather", data)

def compose_email(to: str, weather: Dict[str, Any]) -> Dict[str, str]:
    """
    Return simple email fields: subject and body (strings).
    """
    if isinstance(weather, dict) and "temperature" in weather:
        temp = weather.get("temperature")
        wind = weather.get("windspeed")
        time = weather.get("time")
        subject = f"Weather update — {temp}°C"
        body = (
            f"Hello,\n\n"
            f"Here is the weather for the requested location:\n"
            f"- Temperature: {temp} °C\n"
            f"- Wind speed: {wind} m/s\n"
            f"- Observed at: {time}\n\n"
            "Regards,\nEmail Scheduler (dev)"
        )
    else:
        subject = "Weather update"
        body = f"Hello,\n\nCould not fetch detailed weather.\nRaw: {weather}\n\nRegards,\nEmail Scheduler (dev)"

    return {"to": to, "subject": subject, "body": body}

def send_email_console(email: Dict[str, str]) -> None:
    """
    Mock send — prints the email to console (acts as sending).
    """
    print("\n" + "="*40)
    print("MOCK EMAIL SENT (console)")
    print(f"To: {email['to']}")
    print(f"Subject: {email['subject']}")
    print("Body:")
    print(email["body"])
    print("="*40 + "\n")
