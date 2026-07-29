"""
AI Life Companion — v1 (local prototype)

Gathers Calendar, Tasks, GitHub, Gmail, and weather, then generates an
AI daily brief via Groq. Run with: python companion.py
"""

import os
import datetime
from zoneinfo import ZoneInfo
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_REPO = os.getenv("GITHUB_REPO")  # e.g. "Aarush-04/Vinenti"

LOCAL_TZ_NAME = os.getenv("LOCAL_TIMEZONE", "America/Toronto")
LOCAL_TZ = ZoneInfo(LOCAL_TZ_NAME)

# Caledon, Ontario coordinates — change via .env if you move
WEATHER_LAT = os.getenv("WEATHER_LAT", "43.8709")
WEATHER_LON = os.getenv("WEATHER_LON", "-79.8523")

GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def now_local() -> datetime.datetime:
    return datetime.datetime.now(LOCAL_TZ)


def _format_12h(dt: datetime.datetime) -> str:
    """Portable 12-hour time formatting (avoids %-I, which Windows doesn't support)."""
    hour = dt.hour % 12
    hour = 12 if hour == 0 else hour
    period = "AM" if dt.hour < 12 else "PM"
    return f"{hour}:{dt.strftime('%M')} {period}"


def get_current_time_context() -> str:
    """Human-readable current local date/time — the anchor the AI must use
    for all relative reasoning instead of guessing."""
    now = now_local()
    return f"{now.strftime('%A, %B %d, %Y')}, {_format_12h(now)} ({LOCAL_TZ_NAME})"


# ---------------------------------------------------------------------------
# GitHub activity
# ---------------------------------------------------------------------------
def get_recent_commits():
    """Queries the repo's commit history directly — far more reliable than
    the Events feed, which can lag or under-report pushes. Returns None if
    GITHUB_REPO isn't configured, so the caller can fall back gracefully."""
    if not GITHUB_REPO or not GITHUB_USERNAME:
        return None

    since = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=24)).isoformat()
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    url = f"https://api.github.com/repos/{GITHUB_REPO}/commits"
    params = {"since": since, "author": GITHUB_USERNAME}
    resp = requests.get(url, headers=headers, params=params, timeout=10)
    resp.raise_for_status()
    commits = resp.json()

    if not commits:
        return f"No commits to {GITHUB_REPO} in the last 24 hours."

    messages = [c["commit"]["message"].splitlines()[0] for c in commits]
    return f"{len(commits)} commit(s) to {GITHUB_REPO} in the last 24h: " + "; ".join(messages)


def get_github_activity() -> str:
    """Combines direct commit history (reliable) with the events feed
    (for branch/PR creation signals, best-effort)."""
    if not GITHUB_USERNAME:
        return "GitHub not configured."

    parts = []
    commit_summary = get_recent_commits()
    if commit_summary:
        parts.append(commit_summary)

    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
        url = f"https://api.github.com/users/{GITHUB_USERNAME}/events"
    else:
        url = f"https://api.github.com/users/{GITHUB_USERNAME}/events/public"

    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    events = resp.json()

    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=24)
    for e in events:
        created = datetime.datetime.strptime(
            e["created_at"], "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=datetime.timezone.utc)
        if created < cutoff:
            continue
        etype = e["type"]
        repo = e["repo"]["name"]
        if etype == "CreateEvent":
            parts.append(f"Created {e['payload'].get('ref_type', 'ref')} in {repo}")
        elif etype == "PullRequestEvent":
            parts.append(f"{e['payload'].get('action')} a pull request in {repo}")
        # PushEvents intentionally skipped here — get_recent_commits() is the
        # reliable source for commit counts when GITHUB_REPO is configured.

    if not parts:
        return "No GitHub activity in the last 24 hours."
    return " | ".join(parts)


# ---------------------------------------------------------------------------
# Google Calendar
# ---------------------------------------------------------------------------
def get_calendar_events() -> str:
    """Events over the next 48 hours, labeled Today/Tomorrow in local time
    so the AI never has to do that math itself."""
    try:
        from google_auth import get_calendar_service
    except ImportError:
        return "Calendar module not set up yet."

    try:
        service = get_calendar_service()
    except FileNotFoundError:
        return "Calendar not connected yet (run google_auth.py setup first)."

    now_dt = datetime.datetime.now(datetime.timezone.utc)
    window_end = (now_dt + datetime.timedelta(hours=48)).isoformat()

    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now_dt.isoformat(),
            timeMax=window_end,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    if not events:
        return "No events in the next 48 hours."

    today_date = now_local().date()
    tomorrow_date = today_date + datetime.timedelta(days=1)

    lines = []
    for event in events:
        start_raw = event["start"].get("dateTime", event["start"].get("date"))
        summary = event.get("summary", "Untitled event")

        if "T" in start_raw:
            start_local = datetime.datetime.fromisoformat(start_raw).astimezone(LOCAL_TZ)
            if start_local.date() == today_date:
                label = "Today"
            elif start_local.date() == tomorrow_date:
                label = "Tomorrow"
            else:
                label = start_local.strftime("%a %b %d")
            lines.append(f"{label} {_format_12h(start_local)}: {summary}")
        else:
            event_date = datetime.date.fromisoformat(start_raw)
            label = "Today" if event_date == today_date else "Tomorrow" if event_date == tomorrow_date else event_date.strftime("%a %b %d")
            lines.append(f"{label} (all day): {summary}")

    return "; ".join(lines)


# ---------------------------------------------------------------------------
# Google Tasks
# ---------------------------------------------------------------------------
def get_tasks() -> str:
    """Tasks due today or tomorrow. Compares calendar DATES only — Google
    Tasks never gives a real time-of-day or timezone-aware due instant, so
    trying to do precise datetime math on it is what caused tasks to
    silently disappear before."""
    try:
        from google_auth import get_tasks_service
    except ImportError:
        return "Tasks module not set up yet."

    try:
        service = get_tasks_service()
    except FileNotFoundError:
        return "Tasks not connected yet (run google_auth.py setup first)."

    today_date = now_local().date()
    tomorrow_date = today_date + datetime.timedelta(days=1)

    tasklists = service.tasklists().list().execute().get("items", [])
    due_soon = []

    for tl in tasklists:
        tasks = (
            service.tasks()
            .list(tasklist=tl["id"], showCompleted=False)
            .execute()
            .get("items", [])
        )
        for t in tasks:
            due_str = t.get("due")
            if not due_str:
                continue
            due_date = datetime.date.fromisoformat(due_str[:10])
            if due_date == today_date:
                due_soon.append(f"{t.get('title', 'Untitled task')} (due Today)")
            elif due_date == tomorrow_date:
                due_soon.append(f"{t.get('title', 'Untitled task')} (due Tomorrow)")

    if not due_soon:
        return "No tasks due today or tomorrow."
    return "; ".join(due_soon)


# ---------------------------------------------------------------------------
# Gmail inbox highlights
# ---------------------------------------------------------------------------
def get_inbox_highlights() -> str:
    try:
        from google_auth import get_gmail_service
    except ImportError:
        return "Gmail module not set up yet."

    try:
        service = get_gmail_service()
    except FileNotFoundError:
        return "Gmail not connected yet (run google_auth.py setup first)."

    results = (
        service.users()
        .messages()
        .list(userId="me", q="newer_than:1d", maxResults=10)
        .execute()
    )
    messages = results.get("messages", [])

    if not messages:
        return "No new emails in the last 24 hours."

    highlights = []
    for m in messages:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=m["id"], format="metadata", metadataHeaders=["Subject", "From"])
            .execute()
        )
        headers_list = msg.get("payload", {}).get("headers", [])
        subject = next((h["value"] for h in headers_list if h["name"] == "Subject"), "No subject")
        sender = next((h["value"] for h in headers_list if h["name"] == "From"), "Unknown sender")
        highlights.append(f'"{subject}" from {sender}')

    return "; ".join(highlights)


# ---------------------------------------------------------------------------
# Weather (Open-Meteo — free, no API key required)
# ---------------------------------------------------------------------------
def get_weather() -> str:
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={WEATHER_LAT}&longitude={WEATHER_LON}"
            "&current=temperature_2m"
            "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max"
            f"&temperature_unit=celsius&timezone={LOCAL_TZ_NAME}&forecast_days=2"
        )
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        current_temp = data["current"]["temperature_2m"]
        tomorrow_high = data["daily"]["temperature_2m_max"][1]
        tomorrow_low = data["daily"]["temperature_2m_min"][1]
        rain_chance = data["daily"]["precipitation_probability_max"][1]

        return (
            f"Currently {current_temp}°C. Tomorrow: high {tomorrow_high}°C, "
            f"low {tomorrow_low}°C, {rain_chance}% chance of precipitation."
        )
    except Exception:
        return "Weather unavailable right now."


# ---------------------------------------------------------------------------
# AI daily brief (Groq)
# ---------------------------------------------------------------------------
COMPANION_SYSTEM_PROMPT = """You are a calm, direct AI life companion writing a daily \
brief. You are given the user's CURRENT local date and time — treat this as the fixed \
anchor for all relative reasoning (what counts as "today" vs "tomorrow", how many hours \
until something happens). Never guess the current time yourself; use exactly what's given.

You're also given: calendar events (next 48h, already labeled Today/Tomorrow in local \
time), tasks due today/tomorrow, GitHub activity (last 24h), recent inbox subjects \
(last 24h), and the weather.

Structure the brief in plain prose, under 200 words total:
1. What's actually on deck — merge calendar events and tasks into one clear picture of \
today and tomorrow, by name and time.
2. An honest, specific read on GitHub momentum — say plainly if there's been no activity, \
don't soften a real gap into nothing.
3. Anything worth flagging from the inbox (only if genuinely time-sensitive — job \
responses, interview requests, deadlines — otherwise skip this part).
4. If there's an early event tomorrow (before 9am), work backward from 7-8 hours of \
sleep from the CURRENT time given and state a specific bedtime.
5. If the weather affects tomorrow's plans, mention it briefly.

Be concrete — use the actual names, times, and current-time anchor given, never generic \
filler like "have a great day." No emojis, no corporate tone."""


def generate_daily_brief(
    github_summary: str,
    calendar_summary: str,
    tasks_summary: str = "",
    inbox_summary: str = "",
    weather_summary: str = "",
) -> str:
    if not GROQ_API_KEY:
        return "GROQ_API_KEY not set — add it to your .env file."

    user_content = (
        f"Current local date & time: {get_current_time_context()}\n"
        f"Calendar (next 48h): {calendar_summary}\n"
        f"Tasks due (today/tomorrow): {tasks_summary}\n"
        f"GitHub activity (last 24h): {github_summary}\n"
        f"Recent inbox (last 24h): {inbox_summary}\n"
        f"Weather: {weather_summary}\n\n"
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


if __name__ == "__main__":
    print("Gathering your data...\n")

    github_summary = get_github_activity()
    calendar_summary = get_calendar_events()
    tasks_summary = get_tasks()
    inbox_summary = get_inbox_highlights()
    weather_summary = get_weather()

    print(f"[Time]     {get_current_time_context()}")
    print(f"[GitHub]   {github_summary}")
    print(f"[Calendar] {calendar_summary}")
    print(f"[Tasks]    {tasks_summary}")
    print(f"[Inbox]    {inbox_summary}")
    print(f"[Weather]  {weather_summary}\n")

    print("Generating your daily brief...\n")
    brief = generate_daily_brief(
        github_summary, calendar_summary, tasks_summary, inbox_summary, weather_summary
    )

    print("=" * 50)
    print(brief)
    print("=" * 50)