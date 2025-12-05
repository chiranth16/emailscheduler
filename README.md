##Email Scheduler (Simple FastAPI project)##

This is a small project I made for a backend assignment.
The idea was to create an API where you can schedule an email, and when the time comes, the system checks the weather of that location using the Open-Meteo API and then sends a mock email (it just prints it in the terminal, not real mail).

I mainly used FastAPI for the API part and APScheduler to run the background job that checks the schedules every 30 seconds.

##What the project does (in simple words)
You can add schedules (email + date + time + timezone + location)
At the correct time, it fetches the weather and prints the email content
You can also import schedules from an Excel file
There is also an endpoint to send a test email
It keeps simple logs of emails that were “sent”
Everything is stored in memory (no database)
That’s pretty much it.

##How to run it
Install the required packages:
pip install -r requirements.txt

Start the server:
uvicorn app.main:app --reload --port 8000

Go to:
http://127.0.0.1:8000/docs
This page has all the endpoints and you can test everything from there.

Endpoints (quick list)
/weather → gets weather for given lat/long
/schedules

POST → create schedule
GET → list all
DELETE → remove one
/schedules/import-excel → load from Excel
/send-test-email → just prints an email
/send-logs → shows logs of "sent" emails

##How scheduling works (very simple explanation)

The scheduler runs every 30 seconds in the background.
For each schedule:
It checks if the time in that timezone has passed
If yes:
gets the weather
prepares the mail text
prints it
saves a log
removes the schedule
So once a schedule is created, it automatically sends itself when the time comes.

Example output (what the “email” looks like)
========================================
MOCK EMAIL SENT
To: test@example.com
Subject: Weather update — 24.9°C

Weather:
- Temp: 24.9°C
- Wind: 5.0 m/s

Regards,
Email Scheduler
========================================

Project Structure (rough)
app/
    main.py
    scheduler.py
    mailer.py
    store.py
    excel_reader.py

data/
    sample_schedules.xlsx

requirements.txt
README.md
