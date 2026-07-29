"""
AI Life Companion — v1 (local prototype)

What this does today:
  1. Pulls your GitHub activity for the last 24h (commits/contributions)
  2. Pulls today's Google Calendar events
  3. Sends both to an LLM (via Groq, free tier) with a "companion" persona
  4. Prints your daily brief to the terminal

Run it with:  python companion.py
"""

import os
import datetime
import requests
from dotenv import load_dotenv

load_dotenv()  # reads variables from a local .env file (see .env.example)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")

GROQ_MODEL = "llama-3.3-70b-versatile"  # solid free-tier Groq model as of writing
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


# ---------------------------------------------------------------------------
# 1. GitHub activity
# ---------------------------------------------------------------------------
def get_github_activity() -> str:
    """Returns a short text summary of the user's GitHub activity in the last 24h."""
    if not GITHUB_USERNAME:
        return "GitHub not configured."

    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    url = f"https://api.github.com/users/{GITHUB_USERNAME}/events/public"
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    events = resp.json()

    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=24)
    recent = []
    for e in events:
        created = datetime.datetime.strptime(
            e["created_at"], "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=datetime.timezone.utc)
        if created < cutoff:
            continue
        etype = e["type"]
        repo = e["repo"]["name"]
        if etype == "PushEvent":
            n = len(e["payload"].get("commits", []))
            recent.append(f"Pushed {n} commit(s) to {repo}")
        elif etype == "CreateEvent":
            recent.append(f"Created {e['payload'].get('ref_type', 'ref')} in {repo}")
        elif etype == "PullRequestEvent":
            recent.append(f"{e['payload'].get('action')} a pull request in {repo}")

    if not recent:
        return "No GitHub activity in the last 24 hours."
    return "; ".join(recent)


# ---------------------------------------------------------------------------
# 2. Google Calendar events
# ---------------------------------------------------------------------------
def get_calendar_events() -> str:
    """Returns a short text summary of today's Google Calendar events.
    Requires google_auth.py to have been run once to create token.json.
    """
    try:
        from google_auth import get_calendar_service
    except ImportError:
        return "Calendar module not set up yet."

    try:
        service = get_calendar_service()
    except FileNotFoundError:
        return "Calendar not connected yet (run google_auth.py setup first)."

    now_dt = datetime.datetime.now(datetime.timezone.utc)
    now = now_dt.isoformat()
    end_of_day = now_dt.replace(hour=23, minute=59, second=59).isoformat()

    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            timeMax=end_of_day,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    if not events:
        return "No events left on the calendar today."

    lines = []
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        lines.append(f"{start}: {event.get('summary', 'Untitled event')}")
    return "; ".join(lines)


# ---------------------------------------------------------------------------
# 3. AI daily brief (Groq)
# ---------------------------------------------------------------------------
COMPANION_SYSTEM_PROMPT = """You are a calm, encouraging AI life companion. \
You are not a productivity manager and you never guilt-trip the user. \
You look at their GitHub activity and calendar for the day and give a short, \
warm, practical brief: what's on today, one honest observation about momentum \
(not judgment), and one concrete, small suggestion for the day. \
Keep it under 120 words. No emojis, no corporate tone."""


def generate_daily_brief(github_summary: str, calendar_summary: str) -> str:
    if not GROQ_API_KEY:
        return "GROQ_API_KEY not set — add it to your .env file."

    user_content = (
        f"GitHub activity (last 24h): {github_summary}\n"
        f"Calendar today: {calendar_summary}\n\n"
        "Write today's brief."
    )

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": COMPANION_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.7,
    }
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Gathering your data...\n")

    github_summary = get_github_activity()
    calendar_summary = get_calendar_events()

    print(f"[GitHub]   {github_summary}")
    print(f"[Calendar] {calendar_summary}\n")

    print("Generating your daily brief...\n")
    brief = generate_daily_brief(github_summary, calendar_summary)

    print("=" * 50)
    print(brief)
    print("=" * 50)
