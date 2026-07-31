"""
Local API server for the Vinenti companion app.
Run with: python api_server.py
"""

from flask import Flask, jsonify, request
from flask_cors import CORS

from companion import (
    get_github_context,
    get_calendar_context,
    get_tasks_context,
    get_inbox_context,
    get_weather_context,
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
    length = request.args.get("length", "medium")
    tone = request.args.get("tone", "balanced")

    github_ctx = get_github_context()
    calendar_ctx = get_calendar_context()
    tasks_ctx = get_tasks_context()
    inbox_ctx = get_inbox_context()
    weather_ctx = get_weather_context()

    narrative = generate_daily_brief(
        github_ctx["text"],
        calendar_ctx["summary"],
        tasks_ctx["text"],
        inbox_ctx["text"],
        weather_ctx["text"],
        calendar_ctx["bedtime_advice"],
        length,
        tone,
    )

    return jsonify(
        {
            "narrative": narrative,
            "schedule": calendar_ctx["events"],
            "tasks": {
                "overdue": tasks_ctx["overdue"],
                "today": tasks_ctx["today"],
                "tomorrow": tasks_ctx["tomorrow"],
            },
            "github": {"commit_count": github_ctx["commit_count"], "commits": github_ctx["commits"]},
            "inbox": inbox_ctx["messages"],
            "weather": weather_ctx,
            "bedtime_advice": calendar_ctx["bedtime_advice"],
        }
    )


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    user_message = data.get("message", "")
    history = data.get("history", [])
    tone = data.get("tone", "balanced")

    if not GROQ_API_KEY:
        return jsonify({"reply": "GROQ_API_KEY not set on the server."}), 500

    github_ctx = get_github_context()
    calendar_ctx = get_calendar_context()
    tasks_ctx = get_tasks_context()
    inbox_ctx = get_inbox_context()
    weather_ctx = get_weather_context()
    bedtime_advice = calendar_ctx["bedtime_advice"]
    sleep_line = bedtime_advice if bedtime_advice else "None — do not mention sleep unless asked."

    tone_note = {
        "encouraging": "Be warm and supportive, soften misses.",
        "balanced": "Be calm and direct, honest without harshness.",
        "firm": "Be direct and accountability-focused — call out gaps plainly, but never cruel.",
    }.get(tone, "Be calm and direct.")

    system_content = (
        "You are a calm AI life companion having a conversation with the user. "
        f"{tone_note} Treat the current local date/time below as the fixed anchor "
        "for any relative reasoning — never guess it yourself. If a precomputed "
        "sleep recommendation is given, use it exactly as-is; never calculate your "
        "own bedtime math.\n"
        f"Current local date & time: {get_current_time_context()}\n"
        f"Calendar (next 48h): {calendar_ctx['summary']}\n"
        f"Tasks: {tasks_ctx['text']}\n"
        f"GitHub activity (last 24h): {github_ctx['text']}\n"
        f"Recent inbox (last 24h): {inbox_ctx['text']}\n"
        f"Weather: {weather_ctx['text']}\n"
        f"Precomputed sleep recommendation: {sleep_line}\n\n"
        "Keep replies short and conversational, under 100 words unless the user "
        "is asking for real detail."
    )

    messages = [{"role": "system", "content": system_content}] + history
    messages.append({"role": "user", "content": user_message})

    payload = {"model": GROQ_MODEL, "messages": messages, "temperature": 0.7}
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    reply = resp.json()["choices"][0]["message"]["content"]
    return jsonify({"reply": reply})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)