from flask import Flask, request, Response
from slack_sdk import WebClient
import os

app = Flask(__name__)

# Slack token (set in Render environment variables)
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
client = WebClient(token=SLACK_BOT_TOKEN)

# -----------------------------
# POINT SYSTEM
# -----------------------------
POINT_VALUES = {
    "heart": 1,            # ❤️ like
    "speech_balloon": 5,   # 💬 comment
    "repeat": 4            # 🔁 repost
}

# -----------------------------
# TEAM SYSTEM (edit this)
# -----------------------------
USER_TEAMS = {
    # "U123456": "Blue",
    # "U987654": "Gold",
}

team_scores = {}
user_scores = {}

# -----------------------------
# HOME
# -----------------------------
@app.route("/", methods=["GET"])
def home():
    return "EmojiBot is running!"

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
    # 1. AUTO-REACTIONS ON POSTS
    # -----------------------------
    if event_type == "message":
        channel = event.get("channel")
        ts = event.get("ts")

        try:
            # Add auto reactions
            client.reactions_add(channel=channel, name="fire", timestamp=ts)
            client.reactions_add(channel=channel, name="heart", timestamp=ts)
            client.reactions_add(channel=channel, name="eyes", timestamp=ts)

            print("Auto-reactions added")

        except Exception as e:
            print("Auto-reaction error:", str(e))

    # -----------------------------
    # 2. REACTION GAMIFICATION
    # -----------------------------
    if event_type == "reaction_added":
        user_id = event.get("user")
        reaction = event.get("reaction")

        if reaction in POINT_VALUES:
            points = POINT_VALUES[reaction]

            # Update user score
            user_scores[user_id] = user_scores.get(user_id, 0) + points
            total = user_scores[user_id]

            # Update team score
            team = USER_TEAMS.get(user_id)
            if team:
                team_scores[team] = team_scores.get(team, 0) + points

            try:
                client.chat_postMessage(
                    channel=user_id,
                    text=f"🎮 +{points} points for :{reaction}:!\n🏆 Your total: {total}"
                )
            except Exception as e:
                print("DM error:", str(e))

    # -----------------------------
    # 3. "score" COMMAND
    # -----------------------------
    if event_type == "message":
        text = event.get("text", "").strip().lower()
        channel = event.get("channel")

        if text == "score":

            # Build user leaderboard
            user_board = sorted(
                user_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )

            # Build team leaderboard
            team_board = sorted(
                team_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )

            msg = "*🏆 Current Scores*\n\n"

            msg += "*👤 Top Users:*\n"
            for uid, score in user_board[:5]:
                msg += f"- <@{uid}>: {score} pts\n"

            msg += "\n*👥 Team Scores:*\n"
            for team, score in team_board:
                msg += f"- {team}: {score} pts\n"

            if not team_board:
                msg += "- No team data yet\n"

            try:
                client.chat_postMessage(channel=channel, text=msg)
            except Exception as e:
                print("Score message error:", str(e))

    return Response("", status=200)

# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
