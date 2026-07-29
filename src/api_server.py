"""
Local API server for the Vinenti companion app.

Run with: python api_server.py
Then use the local IP already configured in the mobile app's API_BASE_URL.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS

from companion import (
    get_github_activity,
    get_calendar_events,
    get_tasks,
    get_inbox_highlights,
    get_weather,
    get_current_time_context,
    generate_daily_brief,
    GROQ_API_KEY,
    GROQ_MODEL,
    GROQ_URL,
)
import requests

app = Flask(__name__)
CORS(app)


@app.route("/api/brief", methods=["GET"])
def brief():
    github_summary = get_github_activity()
    calendar_summary = get_calendar_events()
    tasks_summary = get_tasks()
    inbox_summary = get_inbox_highlights()
    weather_summary = get_weather()

    text = generate_daily_brief(
        github_summary, calendar_summary, tasks_summary, inbox_summary, weather_summary
    )
    return jsonify(
        {
            "github": github_summary,
            "calendar": calendar_summary,
            "tasks": tasks_summary,
            "inbox": inbox_summary,
            "weather": weather_summary,
            "brief": text,
        }
    )


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    user_message = data.get("message", "")
    history = data.get("history", [])

    if not GROQ_API_KEY:
        return jsonify({"reply": "GROQ_API_KEY not set on the server."}), 500

    github_summary = get_github_activity()
    calendar_summary = get_calendar_events()
    tasks_summary = get_tasks()
    inbox_summary = get_inbox_highlights()
    weather_summary = get_weather()

    system_content = (
        "You are a calm, direct AI life companion having a conversation with "
        "the user. Treat the current local date/time below as the fixed "
        "anchor for any relative reasoning (today/tomorrow, hours until an "
        "event) — never guess it yourself.\n"
        f"Current local date & time: {get_current_time_context()}\n"
        f"Calendar (next 48h): {calendar_summary}\n"
        f"Tasks due (today/tomorrow): {tasks_summary}\n"
        f"GitHub activity (last 24h): {github_summary}\n"
        f"Recent inbox (last 24h): {inbox_summary}\n"
        f"Weather: {weather_summary}\n\n"
        "Keep replies short and conversational, under 100 words unless the "
        "user is asking for real detail."
    )

    messages = [{"role": "system", "content": system_content}] + history
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.7,
    }
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    reply = resp.json()["choices"][0]["message"]["content"]
    return jsonify({"reply": reply})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)