import os
from flask import Flask, request, Response
from slack_sdk import WebClient
from datetime import datetime

app = Flask(__name__)

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
client = WebClient(token=SLACK_BOT_TOKEN)

# -----------------------------
# STORAGE (MVP)
# -----------------------------
user_scores = {}
weekly_scores = {}

# -----------------------------
# WEEK KEY
# -----------------------------
def get_week_key():
    return datetime.utcnow().isocalendar()[1]

# -----------------------------
# POINT SYSTEM (reactions)
# -----------------------------
POINT_VALUES = {
    "heart": 1,
    "speech_balloon": 5,
    "+1": 4
}

# -----------------------------
# PLATFORM RULES (self-report)
# -----------------------------
PLATFORM_RULES = {
    "instagram": {"like": 1, "comment": 5, "repost": 4, "share": 3, "remix": 6},
    "x": {"like": 1, "comment": 5, "repost": 4},
    "tiktok": {"like": 1, "comment": 5, "repost": 4, "stitch": 7},
    "facebook": {"like": 1, "love": 1, "hug": 1, "comment": 5, "share": 4}
}

# -----------------------------
# SAFE SLACK REACTIONS ONLY
# -----------------------------
PLATFORM_REACTIONS = {
    "instagram": ["heart", "speech_balloon", "+1"],
    "x": ["heart", "speech_balloon", "+1"],
    "tiktok": ["heart", "speech_balloon", "+1"],
    "facebook": ["heart", "speech_balloon", "+1"]
}

# -----------------------------
# HELPERS
# -----------------------------
def add_score(user_id, points):
    user_scores[user_id] = user_scores.get(user_id, 0) + points

    week = get_week_key()
    weekly_scores.setdefault(week, {})
    weekly_scores[week][user_id] = weekly_scores[week].get(user_id, 0) + points

    return user_scores[user_id]


def parse_report(text):
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
    return "Slack Engagement Bot Running"


# -----------------------------
# SLACK EVENTS
# -----------------------------
@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.get_json()

    print("RAW EVENT:", data)

    # Slack URL verification
    if data and data.get("type") == "url_verification":
        return Response(data["challenge"], mimetype="text/plain")

    event = data.get("event", {})

    print("EVENT TYPE:", event.get("type"))
    print("SUBTYPE:", event.get("subtype"))
    print("TEXT:", event.get("text"))

    # -----------------------------
    # GOLD STANDARD FILTER BLOCK
    # -----------------------------
    event_type = event.get("type")

    if event_type not in ["message", "app_mention"]:
        return Response("", status=200)

    if event.get("bot_id"):
        return Response("", status=200)

    if event.get("subtype") in ["bot_message"]:
        return Response("", status=200)

    # -----------------------------
    # MESSAGE DATA
    # -----------------------------
    text = (event.get("text") or "").strip().lower()
    channel = event.get("channel")
    user_id = event.get("user")
    ts = event.get("ts")

    # -----------------------------
    # SCORE COMMAND
    # -----------------------------
    if text == "score":
        week = get_week_key()
        week_data = weekly_scores.get(week, {})

        top_users = sorted(week_data.items(), key=lambda x: x[1], reverse=True)

        msg = "*🏆 Current Weekly Scores*\n\n"

        msg += "*👤 Top Users:*\n"
        if top_users:
            for uid, score in top_users[:5]:
                msg += f"- <@{uid}>: {score} pts\n"
        else:
            msg += "- No data yet\n"

        client.chat_postMessage(channel=channel, text=msg)
        return Response("", status=200)

    # -----------------------------
    # PLATFORM SELF-REPORTING
    # -----------------------------
    platform, action = parse_report(text)

    if platform in PLATFORM_REACTIONS:

        # AUTO-REACTIONS
        for emoji in PLATFORM_REACTIONS[platform]:
            try:
                client.reactions_add(
                    channel=channel,
                    name=emoji,
                    timestamp=ts
                )
            except Exception as e:
                print(f"Reaction error ({emoji}): {e}")

        # SCORING
        if action in PLATFORM_RULES[platform]:
            points = PLATFORM_RULES[platform][action]
            total = add_score(user_id, points)

            client.chat_postMessage(
                channel=channel,
                text=f"📊 {platform} | {action} → +{points} pts (Total: {total})"
            )

    # -----------------------------
    # REACTION GAMIFICATION
    # -----------------------------
    if event_type == "message" and event.get("reactions"):
        pass  # optional future extension

    if event_type == "reaction_added":
        user_id = event.get("user")
        reaction = event.get("reaction")

        if reaction in POINT_VALUES:
            points = POINT_VALUES[reaction]
            total = add_score(user_id, points)

            try:
                client.chat_postMessage(
                    channel=user_id,
                    text=f"🎮 +{points} (: {reaction} :) → Total: {total}"
                )
            except Exception as e:
                print("DM error:", e)

    return Response("", status=200)


# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
