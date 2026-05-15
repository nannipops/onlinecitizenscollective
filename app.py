import os
from flask import Flask, request, Response
from slack_sdk import WebClient

app = Flask(__name__)

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
client = WebClient(token=SLACK_BOT_TOKEN)

# -----------------------------
# SCORE STORAGE (MVP - in memory)
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
# PLATFORM → ALLOWED REACTIONS
# (Slack-safe emoji names)
# -----------------------------
PLATFORM_REACTIONS = {
    "instagram": ["heart", "speech_balloon", "repeat", "link", "tv"],
    "x": ["heart", "speech_balloon", "repeat"],
    "tiktok": ["heart", "speech_balloon", "repeat", "tv"],
    "facebook": ["heart", "speech_balloon", "repeat"]
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
    return "EmojiBot with platform gamification running"


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

    if "event" not in data:
        return Response("", status=200)

    event = data["event"]

    # Ignore bot messages
    if event.get("bot_id") or event.get("subtype") == "bot_message":
        return Response("", status=200)

    event_type = event.get("type")

    # -----------------------------
    # MESSAGE EVENTS
    # -----------------------------
    if event_type == "message":
        text = event.get("text", "").strip().lower()
        channel = event.get("channel")
        user_id = event.get("user")
        ts = event.get("ts")

        # -------------------------
        # SCORE COMMAND
        # -------------------------
        if text == "score":
            score = user_scores.get(user_id, 0)

            client.chat_postMessage(
                channel=channel,
                text=f"🏆 Your score: *{score}*"
            )
            return Response("", status=200)

        # -------------------------
        # SELF-REPORTED ENGAGEMENT
        # -------------------------
        platform, action = parse_report(text)

        if platform in PLATFORM_REACTIONS:
            reactions = PLATFORM_REACTIONS[platform]

            # Auto-react based on platform rules
            for emoji in reactions:
                try:
                    client.reactions_add(
                        channel=channel,
                        name=emoji,
                        timestamp=ts
                    )
                except Exception as e:
                    print(f"Reaction error ({emoji}):", e)

            # Simple scoring from action type
            # (you can expand this later)
            base_points = {
                "like": 1,
                "comment": 5,
                "repost": 4,
                "share": 4,
                "stitch": 7,
                "remix": 6,
                "reel": 6
            }

            if action in base_points:
                points = base_points[action]
                total = add_score(user_id, points)

                client.chat_postMessage(
                    channel=channel,
                    text=(
                        f"📊 Logged: *{platform} | {action}*\n"
                        f"+{points} points → Total: *{total}*"
                    )
                )

    # -----------------------------
    # REACTION GAMIFICATION
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
                    text=f"🎮 +{points} for :{reaction}: → Total: {total}"
                )
            except Exception as e:
                print("DM error:", e)

    return Response("", status=200)


# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
