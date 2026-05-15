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
# POINT SYSTEM (reactions)
# -----------------------------
POINT_VALUES = {
    "heart": 1,
    "speech_balloon": 5,
    "repeat": 4
}

# -----------------------------
# SELF-REPORT SYSTEM
# -----------------------------
PLATFORM_RULES = {
    "instagram": {"like": 1, "comment": 5, "repost": 4, "share": 3, "remix": 6},
    "x": {"like": 1, "comment": 5, "repost": 4},
    "tiktok": {"like": 1, "comment": 5, "repost": 4, "stitch": 7},
    "facebook": {"like": 1, "love": 1, "comment": 5, "share": 4}
}

def add_score(user_id, points):
    user_scores[user_id] = user_scores.get(user_id, 0) + points
    return user_scores[user_id]

def parse_report(text):
    if "|" not in text:
        return None, None
    p = [x.strip().lower() for x in text.split("|")]
    return (p[0], p[1]) if len(p) == 2 else (None, None)

# -----------------------------
# HOME
# -----------------------------
@app.route("/", methods=["GET"])
def home():
    return "EmojiBot running"

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
    event_type = event.get("type")

    # Ignore bot messages
    if event.get("bot_id") or event.get("subtype") == "bot_message":
        return Response("", status=200)

    # -----------------------------
    # 1. AUTO REACTIONS ON POSTS
    # -----------------------------
    if event_type == "message":
        channel = event.get("channel")
        ts = event.get("ts")

        try:
            client.reactions_add(channel=channel, name="heart", timestamp=ts)
            client.reactions_add(channel=channel, name="fire", timestamp=ts)
            client.reactions_add(channel=channel, name="eyes", timestamp=ts)
        except Exception as e:
            print("Auto-react error:", e)

        # -------------------------
        # SCORE COMMAND
        # -------------------------
        text = event.get("text", "").strip().lower()
        user_id = event.get("user")

        if text == "score" and user_id:
            score = user_scores.get(user_id, 0)
            client.chat_postMessage(
                channel=channel,
                text=f"🏆 Your score: *{score}*"
            )

        # -------------------------
        # SELF REPORT LOGGING
        # -------------------------
        platform, action = parse_report(text)

        if platform in PLATFORM_RULES and action in PLATFORM_RULES[platform]:
            points = PLATFORM_RULES[platform][action]
            total = add_score(user_id, points)

            client.chat_postMessage(
                channel=channel,
                text=f"📊 {platform} | {action} → +{points} pts (Total: {total})"
            )

    # -----------------------------
    # 2. REACTION GAMIFICATION
    # -----------------------------
    if event_type == "reaction_added":
        user_id = event.get("user")
        reaction = event.get("reaction")

        if reaction in POINT_VALUES:
            points = POINT_VALUES[reaction]
            total = add_score(user_id, points)

            try:
                client.chat_postMessage(
                    channel=user_id,
                    text=f"🎮 +{points} for :{reaction}: → Total {total}"
                )
            except Exception as e:
                print("DM error:", e)

    return Response("", status=200)

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
