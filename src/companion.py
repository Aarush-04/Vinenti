"""
AI Life Companion — v1 backend logic.

Gathers Calendar, Tasks, GitHub, Gmail, and weather as STRUCTURED data
(for the app to render as widgets), plus a short AI narrative that adapts
to the user's chosen length/tone preference.
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
GITHUB_REPO = os.getenv("GITHUB_REPO")

LOCAL_TZ_NAME = os.getenv("LOCAL_TIMEZONE", "America/Toronto")
LOCAL_TZ = ZoneInfo(LOCAL_TZ_NAME)

WEATHER_LAT = os.getenv("WEATHER_LAT", "43.8709")
WEATHER_LON = os.getenv("WEATHER_LON", "-79.8523")

GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def now_local() -> datetime.datetime:
    return datetime.datetime.now(LOCAL_TZ)


def _format_12h(dt: datetime.datetime) -> str:
    hour = dt.hour % 12
    hour = 12 if hour == 0 else hour
    period = "AM" if dt.hour < 12 else "PM"
    return f"{hour}:{dt.strftime('%M')} {period}"


def get_current_time_context() -> str:
    now = now_local()
    return f"{now.strftime('%A, %B %d, %Y')}, {_format_12h(now)} ({LOCAL_TZ_NAME})"


# ---------------------------------------------------------------------------
# GitHub
# ---------------------------------------------------------------------------
def _get_recently_active_repos(limit=3):
    if not GITHUB_TOKEN:
        return []
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
    }
    resp = requests.get(
        "https://api.github.com/user/repos",
        headers=headers,
        params={"sort": "pushed", "direction": "desc", "per_page": limit},
        timeout=10,
    )
    resp.raise_for_status()
    return [r["full_name"] for r in resp.json()]


def get_github_context() -> dict:
    """Structured GitHub activity: {commit_count, commits: [{repo, message}], text}"""
    if not GITHUB_USERNAME:
        return {"commit_count": 0, "commits": [], "text": "GitHub not configured."}

    if GITHUB_REPO:
        repos_to_check = [r.strip() for r in GITHUB_REPO.split(",") if r.strip()]
    else:
        repos_to_check = _get_recently_active_repos()

    if not repos_to_check:
        return {"commit_count": 0, "commits": [], "text": "No GitHub activity in the last 24 hours."}

    since = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=24)).isoformat()
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    commits = []
    for repo in repos_to_check:
        resp = requests.get(
            f"https://api.github.com/repos/{repo}/commits",
            headers=headers,
            params={"since": since, "author": GITHUB_USERNAME},
            timeout=10,
        )
        if resp.status_code != 200:
            continue
        for c in resp.json():
            commits.append({"repo": repo, "message": c["commit"]["message"].splitlines()[0]})

    if not commits:
        checked = ", ".join(repos_to_check)
        text = f"No commits in the last 24 hours (checked: {checked})."
    else:
        text = f"{len(commits)} commit(s) in the last 24h: " + "; ".join(
            f"{c['repo']}: {c['message']}" for c in commits
        )

    return {"commit_count": len(commits), "commits": commits, "text": text}


def get_github_activity() -> str:
    return get_github_context()["text"]


# ---------------------------------------------------------------------------
# Google Calendar
# ---------------------------------------------------------------------------
def get_calendar_context() -> dict:
    """Returns {events: [{label, time, summary, all_day}], summary, bedtime_advice}"""
    try:
        from google_auth import get_calendar_service
    except ImportError:
        return {"events": [], "summary": "Calendar module not set up yet.", "bedtime_advice": None}

    try:
        service = get_calendar_service()
    except FileNotFoundError:
        return {
            "events": [],
            "summary": "Calendar not connected yet (run google_auth.py setup first).",
            "bedtime_advice": None,
        }

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
    raw_events = events_result.get("items", [])

    if not raw_events:
        return {"events": [], "summary": "No events in the next 48 hours.", "bedtime_advice": None}

    today_date = now_local().date()
    tomorrow_date = today_date + datetime.timedelta(days=1)

    events = []
    earliest_early_event = None

    for event in raw_events:
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
            events.append({"label": label, "time": _format_12h(start_local), "summary": summary, "all_day": False})

            if start_local.date() == tomorrow_date and start_local.hour < 9:
                if earliest_early_event is None or start_local < earliest_early_event[0]:
                    earliest_early_event = (start_local, summary)
        else:
            event_date = datetime.date.fromisoformat(start_raw)
            label = "Today" if event_date == today_date else "Tomorrow" if event_date == tomorrow_date else event_date.strftime("%a %b %d")
            events.append({"label": label, "time": None, "summary": summary, "all_day": True})

    bedtime_advice = None
    if earliest_early_event:
        event_dt, event_name = earliest_early_event
        bedtime = event_dt - datetime.timedelta(hours=7, minutes=30)
        bedtime_advice = (
            f"Tomorrow's earliest event is {event_name} at {_format_12h(event_dt)}. "
            f"To get 7-8 hours of sleep, aim to be asleep by around {_format_12h(bedtime)} tonight."
        )

    summary_text = "; ".join(f"{e['label']} {e['time'] or '(all day)'}: {e['summary']}" for e in events)
    return {"events": events, "summary": summary_text, "bedtime_advice": bedtime_advice}


def get_calendar_events() -> str:
    return get_calendar_context()["summary"]


# ---------------------------------------------------------------------------
# Google Tasks
# ---------------------------------------------------------------------------
def get_tasks_context() -> dict:
    """Returns {overdue: [...], today: [...], tomorrow: [...]}"""
    try:
        from google_auth import get_tasks_service
    except ImportError:
        return {"overdue": [], "today": [], "tomorrow": [], "text": "Tasks module not set up yet."}

    try:
        service = get_tasks_service()
    except FileNotFoundError:
        return {"overdue": [], "today": [], "tomorrow": [], "text": "Tasks not connected yet."}

    today_date = now_local().date()
    tomorrow_date = today_date + datetime.timedelta(days=1)

    tasklists = service.tasklists().list().execute().get("items", [])
    overdue, today_tasks, tomorrow_tasks = [], [], []

    for tl in tasklists:
        tasks = service.tasks().list(tasklist=tl["id"], showCompleted=False).execute().get("items", [])
        for t in tasks:
            due_str = t.get("due")
            if not due_str:
                continue
            due_date = datetime.date.fromisoformat(due_str[:10])
            title = t.get("title", "Untitled task")
            if due_date == today_date:
                today_tasks.append(title)
            elif due_date == tomorrow_date:
                tomorrow_tasks.append(title)
            elif due_date < today_date:
                overdue.append(title)

    parts = []
    if overdue:
        parts.append(f"Overdue (still worth doing): {', '.join(overdue)}")
    if today_tasks:
        parts.append(f"Due today: {', '.join(today_tasks)}")
    if tomorrow_tasks:
        parts.append(f"Due tomorrow: {', '.join(tomorrow_tasks)}")
    text = " | ".join(parts) if parts else "No tasks due today or tomorrow, and nothing overdue."

    return {"overdue": overdue, "today": today_tasks, "tomorrow": tomorrow_tasks, "text": text}


def get_tasks() -> str:
    return get_tasks_context()["text"]


# ---------------------------------------------------------------------------
# Gmail
# ---------------------------------------------------------------------------
def get_inbox_context() -> dict:
    """Returns {messages: [{subject, sender}], text}"""
    try:
        from google_auth import get_gmail_service
    except ImportError:
        return {"messages": [], "text": "Gmail module not set up yet."}

    try:
        service = get_gmail_service()
    except FileNotFoundError:
        return {"messages": [], "text": "Gmail not connected yet."}

    results = service.users().messages().list(userId="me", q="newer_than:1d", maxResults=10).execute()
    message_refs = results.get("messages", [])

    if not message_refs:
        return {"messages": [], "text": "No new emails in the last 24 hours."}

    messages = []
    for m in message_refs:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=m["id"], format="metadata", metadataHeaders=["Subject", "From"])
            .execute()
        )
        headers_list = msg.get("payload", {}).get("headers", [])
        subject = next((h["value"] for h in headers_list if h["name"] == "Subject"), "No subject")
        sender = next((h["value"] for h in headers_list if h["name"] == "From"), "Unknown sender")
        messages.append({"subject": subject, "sender": sender})

    text = "; ".join(f'"{m["subject"]}" from {m["sender"]}' for m in messages)
    return {"messages": messages, "text": text}


def get_inbox_highlights() -> str:
    return get_inbox_context()["text"]


# ---------------------------------------------------------------------------
# Weather
# ---------------------------------------------------------------------------
def get_weather_context() -> dict:
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
        today_high = data["daily"]["temperature_2m_max"][0]
        tomorrow_high = data["daily"]["temperature_2m_max"][1]
        tomorrow_low = data["daily"]["temperature_2m_min"][1]
        rain_chance = data["daily"]["precipitation_probability_max"][1]

        diff = round(tomorrow_high - today_high)
        if diff >= 2:
            comparison = f"{diff}°C warmer than today"
        elif diff <= -2:
            comparison = f"{abs(diff)}°C cooler than today"
        else:
            comparison = "about the same as today"

        text = (
            f"Currently {current_temp}°C. Tomorrow: high {tomorrow_high}°C "
            f"({comparison}), low {tomorrow_low}°C, {rain_chance}% chance of precipitation."
        )
        return {
            "current_temp": current_temp,
            "tomorrow_high": tomorrow_high,
            "tomorrow_low": tomorrow_low,
            "rain_chance": rain_chance,
            "comparison": comparison,
            "text": text,
        }
    except Exception:
        return {"text": "Weather unavailable right now."}


def get_weather() -> str:
    return get_weather_context()["text"]


# ---------------------------------------------------------------------------
# AI narrative (Groq) — adapts to length + tone preference
# ---------------------------------------------------------------------------
LENGTH_GUIDANCE = {
    "short": "Under 40 words. One sentence on momentum, one on what matters most next.",
    "medium": "Under 90 words. Momentum read, the single most important thing to focus on, sleep/weather notes if applicable.",
    "long": "Under 160 words. Full momentum read, inbox context if time-sensitive, sleep/weather notes, and encouragement or accountability framing as appropriate.",
}

TONE_GUIDANCE = {
    "encouraging": "Warm and supportive. Soften misses, lead with progress, never blunt about gaps.",
    "balanced": "Calm and direct. Honest about gaps without softening them into nothing, but not harsh.",
    "firm": "Direct and accountability-focused. Call out missed tasks and stale GitHub activity plainly, no cushioning — but never cruel or demeaning.",
}


def generate_daily_brief(
    github_summary: str,
    calendar_summary: str,
    tasks_summary: str = "",
    inbox_summary: str = "",
    weather_summary: str = "",
    bedtime_advice: str = None,
    length: str = "medium",
    tone: str = "balanced",
) -> str:
    if not GROQ_API_KEY:
        return "GROQ_API_KEY not set — add it to your .env file."

    length_rule = LENGTH_GUIDANCE.get(length, LENGTH_GUIDANCE["medium"])
    tone_rule = TONE_GUIDANCE.get(tone, TONE_GUIDANCE["balanced"])
    sleep_line = bedtime_advice if bedtime_advice else "None — do not mention sleep at all."

    system_prompt = f"""You are a calm AI life companion writing a short narrative that \
accompanies a structured briefing screen. The user ALREADY sees the full schedule, task \
list, and inbox as separate visual widgets elsewhere in the app — your job is NOT to \
repeat that list. Write only the connective insight: an honest read on momentum, what to \
prioritize, and sleep/weather notes if applicable.

Length: {length_rule}
Tone: {tone_rule}

Rules:
- Never invent or recalculate a bedtime — only state the precomputed sleep line exactly \
as given, and only if one is provided.
- Never list out every task/event by name — that's already shown elsewhere. Reference at \
most one specific thing if it's the single most important item.
- Use the current local date/time given as the fixed anchor for any relative reasoning.
- No emojis, no corporate tone, no generic filler."""

    user_content = (
        f"Current local date & time: {get_current_time_context()}\n"
        f"Calendar (next 48h): {calendar_summary}\n"
        f"Tasks: {tasks_summary}\n"
        f"GitHub activity (last 24h): {github_summary}\n"
        f"Recent inbox (last 24h): {inbox_summary}\n"
        f"Weather: {weather_summary}\n"
        f"Precomputed sleep recommendation: {sleep_line}\n\n"
        "Write the narrative."
    )

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.7,
    }
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}

    resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


if __name__ == "__main__":
    print("Gathering your data...\n")
    github_ctx = get_github_context()
    calendar_ctx = get_calendar_context()
    tasks_ctx = get_tasks_context()
    inbox_ctx = get_inbox_context()
    weather_ctx = get_weather_context()

    print(f"[Time]     {get_current_time_context()}")
    print(f"[GitHub]   {github_ctx['text']}")
    print(f"[Calendar] {calendar_ctx['summary']}")
    print(f"[Tasks]    {tasks_ctx['text']}")
    print(f"[Inbox]    {inbox_ctx['text']}")
    print(f"[Weather]  {weather_ctx['text']}\n")

    print("Generating your daily brief...\n")
    brief = generate_daily_brief(
        github_ctx["text"],
        calendar_ctx["summary"],
        tasks_ctx["text"],
        inbox_ctx["text"],
        weather_ctx["text"],
        calendar_ctx["bedtime_advice"],
    )
    print("=" * 50)
    print(brief)
    print("=" * 50)