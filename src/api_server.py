"""
Local API server for the Vinenti companion app.

Wraps the same logic from companion.py (GitHub + Calendar + Groq) behind
a simple HTTP API so the Expo app on your phone can call it — as long as
your phone and PC are on the same WiFi network. No hosting, no cost.

Run with:  python api_server.py
Then find your PC's local IP (see README_MOBILE.md) and use that in the
Expo app's config.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS

from companion import (
    get_github_activity,
    get_calendar_events,
    generate_daily_brief,
    GROQ_API_KEY,
    GROQ_MODEL,
    GROQ_URL,
)
import requests

app = Flask(__name__)
CORS(app)  # allows the phone app (different device) to call this API


@app.route("/api/brief", methods=["GET"])
def brief():
    github_summary = get_github_activity()
    calendar_summary = get_calendar_events()
    text = generate_daily_brief(github_summary, calendar_summary)
    return jsonify(
        {
            "github": github_summary,
            "calendar": calendar_summary,
            "brief": text,
        }
    )


@app.route("/api/chat", methods=["POST"])
def chat():
    """Free-form chat with the companion AI."""
    data = request.get_json(force=True)
    user_message = data.get("message", "")

    if not GROQ_API_KEY:
        return jsonify({"reply": "GROQ_API_KEY not set on the server."}), 500

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a calm, encouraging AI life companion chatting "
                    "with the user. Keep replies short and conversational."
                ),
            },
            {"role": "user", "content": user_message},
        ],
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
    # host="0.0.0.0" makes it reachable from other devices on the same WiFi
    app.run(host="0.0.0.0", port=5000, debug=True)
