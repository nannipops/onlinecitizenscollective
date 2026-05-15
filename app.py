from flask import Flask, request, Response
from slack_sdk import WebClient
import os

app = Flask(__name__)

# Slack Bot Token from Render environment variables
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")

# Initialize Slack client
client = WebClient(token=SLACK_BOT_TOKEN)

# -----------------------------------
# POINT SYSTEM
# -----------------------------------

# Emoji → point values
POINT_VALUES = {
    "heart": 1,            # ❤️ Like
    "speech_balloon": 5,   # 💬 Comment
    "repeat": 4            # 🔁 Repost / Retweet
}

# Basic in-memory score tracker
# (Later we can upgrade to a database)
user_scores = {}


# -----------------------------------
# HOME ROUTE
# -----------------------------------

@app.route("/", methods=["GET"])
def home():
    return "Slack Engagement Bot is running!"


# -----------------------------------
# SLACK EVENTS ROUTE
# -----------------------------------

@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.get_json()

    print("RAW EVENT:", data)

    # -----------------------------------
    # Slack URL Verification
    # -----------------------------------
    if data and data.get("type") == "url_verification":
        return Response(data["challenge"], mimetype="text/plain")

    # -----------------------------------
    # Handle Slack Events
    # -----------------------------------
    if "event" in data:
        event = data["event"]

        # Ignore bot messages
        if event.get("bot_id"):
            return Response("", status=200)

        # -----------------------------------
        # Reaction Added Event
        # -----------------------------------
        if event.get("type") == "reaction_added":
            user_id = event.get("user")
            reaction = event.get("reaction")

            print(f"Reaction detected: {reaction} from {user_id}")

            # Only score tracked reactions
            if reaction in POINT_VALUES:
                points = POINT_VALUES[reaction]

                # Add points to user's total
                user_scores[user_id] = user_scores.get(user_id, 0) + points
                total_points = user_scores[user_id]

                try:
                    # Send DM to user with updated score
                    client.chat_postMessage(
                        channel=user_id,
                        text=(
                            f"🎮 You earned +{points} points for :{reaction}:!\n"
                            f"🏆 Your total score is now *{total_points}* points."
                        )
                    )

                    print(f"Successfully added {points} points to {user_id}")

                except Exception as e:
                    print("Message error:", str(e))

    return Response("", status=200)


# -----------------------------------
# RUN APP
# -----------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
