from flask import Flask, request, Response
from slack_sdk import WebClient
import os

app = Flask(__name__)

client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])

# ----------------------------
# Emoji rules
# ----------------------------
REACTIONS = {
    "instagram.com": ["heart", "speech_balloon", "repeat", "outbox_tray", "clapper"],
    "x.com": ["heart", "speech_balloon", "repeat"],
    "twitter.com": ["heart", "speech_balloon", "repeat"],
    "tiktok.com": ["heart", "speech_balloon", "repeat", "scissors"]
}

# ----------------------------
# Slack Events endpoint
# ----------------------------
@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.get_json(silent=True)

    # 🔍 DEBUG: see everything Slack sends
    print("RAW EVENT:", data)

    # ----------------------------
    # Slack URL verification handshake
    # ----------------------------
    if data and data.get("type") == "url_verification":
        return Response(data["challenge"], mimetype="text/plain")

    # ----------------------------
    # Event handling
    # ----------------------------
    if data and "event" in data:
        event = data["event"]

        print("EVENT OBJECT:", event)

        # Ignore bot messages
        if event.get("bot_id"):
            return Response("", status=200)

        text = ""

        # Normal message text
        if event.get("text"):
            text += event["text"].lower()

        # Block-based messages (RSS feeds often use this)
        blocks = event.get("blocks", [])
        for block in blocks:
            if block.get("type") == "rich_text":
                for elem in block.get("elements", []):
                    for item in elem.get("elements", []):
                        if item.get("type") == "text":
                            text += item.get("text", "").lower()

        channel = event.get("channel")
        ts = event.get("ts")

        print("PARSED TEXT:", text)

        # ----------------------------
        # Detect platform + react
        # ----------------------------
        for platform, emojis in REACTIONS.items():
            if platform in text:
                print(f"MATCH FOUND: {platform}")

                for emoji in emojis:
                    try:
                        client.reactions_add(
                            channel=channel,
                            timestamp=ts,
                            name=emoji
                        )
                        print(f"Added emoji: {emoji}")
                    except Exception as e:
                        print("Reaction error:", e)

    return Response("", status=200)


# ----------------------------
# Health check (Render)
# ----------------------------
@app.route("/")
def home():
    return "EmojiBot is live"


# ----------------------------
# Local run (Render ignores this)
# ----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
