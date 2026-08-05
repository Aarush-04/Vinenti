"""
Local API server for the Vinenti companion app.
Run with: python api_server.py
"""

import re
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
    add_task,
    update_task_due,
    complete_task,
    uncomplete_task,
    now_local,
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
                "completed_today": tasks_ctx["completed_today"],
            },
            "github": {"commit_count": github_ctx["commit_count"], "commits": github_ctx["commits"]},
            "inbox": inbox_ctx["messages"],
            "weather": weather_ctx,
            "bedtime_advice": calendar_ctx["bedtime_advice"],
        }
    )


@app.route("/api/tasks/add", methods=["POST"])
def tasks_add():
    data = request.get_json(force=True)
    title = data.get("title", "").strip()
    due_date = data.get("due")
    if not title:
        return jsonify({"error": "title is required"}), 400
    result = add_task(title, due_date)
    return jsonify(result)


@app.route("/api/tasks/update", methods=["POST"])
def tasks_update():
    data = request.get_json(force=True)
    tasklist_id = data.get("tasklist_id")
    task_id = data.get("task_id")
    due_date = data.get("due")
    if not tasklist_id or not task_id or not due_date:
        return jsonify({"error": "tasklist_id, task_id, and due are required"}), 400
    update_task_due(tasklist_id, task_id, due_date)
    return jsonify({"updated": True})


@app.route("/api/tasks/complete", methods=["POST"])
def tasks_complete():
    data = request.get_json(force=True)
    tasklist_id = data.get("tasklist_id")
    task_id = data.get("task_id")
    if not tasklist_id or not task_id:
        return jsonify({"error": "tasklist_id and task_id are required"}), 400
    complete_task(tasklist_id, task_id)
    return jsonify({"completed": True})


@app.route("/api/tasks/uncomplete", methods=["POST"])
def tasks_uncomplete():
    data = request.get_json(force=True)
    tasklist_id = data.get("tasklist_id")
    task_id = data.get("task_id")
    if not tasklist_id or not task_id:
        return jsonify({"error": "tasklist_id and task_id are required"}), 400
    uncomplete_task(tasklist_id, task_id)
    return jsonify({"uncompleted": True})


# The AI ends its reply with one of these markers (on its own line) when it
# detects a task action. The server executes the real action and strips
# the marker before showing the reply.
ADD_TASK_RE = re.compile(r"\[\[ADD_TASK:\s*(.+?)\]\]")
UPDATE_TASK_RE = re.compile(r"\[\[UPDATE_TASK:\s*(.+?)\s*->\s*(\d{4}-\d{2}-\d{2})\]\]")


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

    # Give the model the exact existing task titles, so it can choose to
    # UPDATE one instead of blindly creating a duplicate.
    all_open_tasks = tasks_ctx["overdue"] + tasks_ctx["today"] + tasks_ctx["tomorrow"]
    existing_titles = ", ".join(f'"{t["title"]}"' for t in all_open_tasks) or "none"

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
        f"Existing open task titles (exact): {existing_titles}\n"
        f"GitHub activity (last 24h): {github_ctx['text']}\n"
        f"Recent inbox (last 24h): {inbox_ctx['text']}\n"
        f"Weather: {weather_ctx['text']}\n"
        f"Precomputed sleep recommendation: {sleep_line}\n\n"
        "Keep replies short and conversational, under 100 words unless the user "
        "is asking for real detail.\n\n"
        "TASK ACTIONS — use exactly one of these, only when clearly warranted:\n"
        "1. If the user describes a NEW to-do not already in the existing task "
        "titles list, end your reply with a new line: "
        "[[ADD_TASK: <short task title>]]\n"
        "2. If the user is correcting or rescheduling a task that's already in "
        "the existing task titles list (e.g. \"fix that\", \"move it to "
        "tomorrow\", \"that should be due Aug 1st\"), do NOT create a new task — "
        "instead end your reply with: "
        "[[UPDATE_TASK: <exact existing title> -> <YYYY-MM-DD>]]\n"
        "Use the current date given above to resolve relative dates like "
        "\"tomorrow\" correctly. Never mention these marker formats to the user."
    )

    messages = [{"role": "system", "content": system_content}] + history
    messages.append({"role": "user", "content": user_message})

    payload = {"model": GROQ_MODEL, "messages": messages, "temperature": 0.7}
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    reply = resp.json()["choices"][0]["message"]["content"]

    action_note = None

    update_match = UPDATE_TASK_RE.search(reply)
    add_match = ADD_TASK_RE.search(reply)

    if update_match:
        old_title, new_due = update_match.group(1).strip(), update_match.group(2).strip()
        target = next(
            (t for t in all_open_tasks if t["title"].strip().lower() == old_title.lower()), None
        )
        if not target:
            # loose fallback match if exact match fails
            target = next(
                (t for t in all_open_tasks if old_title.lower() in t["title"].lower()), None
            )
        if target:
            try:
                update_task_due(target["tasklist_id"], target["id"], new_due)
                action_note = f'(Rescheduled "{target["title"]}" to {new_due}.)'
            except Exception:
                action_note = None
        reply = UPDATE_TASK_RE.sub("", reply).strip()

    elif add_match:
        task_title = add_match.group(1).strip()
        try:
            add_task(task_title)
            action_note = f'(Added "{task_title}" to your tasks.)'
        except Exception:
            action_note = None
        reply = ADD_TASK_RE.sub("", reply).strip()

    if action_note:
        reply += f"\n\n{action_note}"

    return jsonify({"reply": reply})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)