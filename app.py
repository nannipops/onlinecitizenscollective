from flask import Flask, request, Response
from slack_sdk import WebClient
import os

app = Flask(__name__)

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
client = WebClient(token=SLACK_BOT_TOKEN)

# -----------------------------
# SCORE STORAGE (MVP)
# -----------------------------
user_scores = {}

# -----------------------------
# PLATFORM SCORING RULES
# -----------------------------
PLATFORM_RULES = {
    "instagram": {
        "like": 1,
        "comment": 5,
        "repost": 4,
        "share": 3,
        "remix": 6,
        "reel": 6
    },
    "x": {
        "like": 1,
        "comment": 5,
        "repost": 4
    },
    "tiktok": {
        "like": 1,
        "comment": 5,
        "repost": 4,
        "stitch": 7
    },
    "facebook": {
        "like": 1,
        "love": 1,
        "hug": 1,
        "comment": 5,
        "share": 4
    }
}

# -----------------------------
# HELPERS
# -----------------------------
def add_score(user_id, points):
    user_scores[user_id] = user_scores.get(user_id, 0) + points
    return user_scores[user_id]

def parse_report(text):
    """
    Expected format:
    platform | action
    """
    if "|" not in text:
        return None, None

    parts = [p.strip().lower() for p in text.split("|")]
    if len(parts) != 2:
        return None, None

    return parts[0], parts[1]

# -----------------------------
# HOME
# -----------------------------
@app.route("/", methods=["GET"])
def home():
    return "Self-Reported Gamification Bot Running"

# -----------------------------
# SLACK EVENTS
# -----------------------------
@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.get_json()

    print("RAW EVENT:", data)

    if data and data.get("type") == "url_verification":
        return Response(data["challenge"], mimetype="text/plain")

    if "event" not in data:
        return Response("", status=200)

    event = data["event"]

    # ignore bot messages
    if event.get("bot_id") or event.get("subtype") == "bot_message":
        return Response("", status=200)

    if event.get("type") != "message":
        return Response("", status=200)

    user_id = event.get("user")
    channel = event.get("channel")
    text = event.get("text", "").strip().lower()

    # -----------------------------
    # SCORE COMMAND
    # -----------------------------
    if text == "score":
        score = user_scores.get(user_id, 0)

        client.chat_postMessage(
            channel=channel,
            text=f"🏆 Your current score: *{score}* points"
        )
        return Response("", status=200)

    # -----------------------------
    # SELF-REPORTED ENGAGEMENT
    # -----------------------------
    platform, action = parse_report(text)

    if platform in PLATFORM_RULES:
        rules = PLATFORM_RULES[platform]

        if action in rules:
            points = rules[action]
            total = add_score(user_id, points)

            client.chat_postMessage(
                channel=channel,
                text=(
                    f"📊 Logged: *{platform} | {action}*\n"
                    f"+{points} points added\n"
                    f"🏆 Total score: *{total}*"
                )
            )
        else:
            client.chat_postMessage(
                channel=channel,
                text=f"⚠️ Unknown action for {platform}. Try: {', '.join(rules.keys())}"
            )

    return Response("", status=200)

# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
