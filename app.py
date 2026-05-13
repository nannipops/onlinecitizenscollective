from flask import Flask, request, Response

app = Flask(__name__)

# ----------------------------
# Slack URL Verification + Event Handler
# ----------------------------
@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.get_json(silent=True)

    # 1. Slack URL verification challenge (REQUIRED)
    if data and data.get("type") == "url_verification":
        return Response(data["challenge"], mimetype="text/plain")

    # 2. Event handling placeholder (we'll expand this later)
    if data and data.get("type") == "event_callback":
        event = data.get("event", {})
        print("Received event:", event)

    return Response("", status=200)


# ----------------------------
# Health check (Render test)
# ----------------------------
@app.route("/")
def home():
    return "Bot is alive"


# ----------------------------
# Run locally (Render ignores this)
# ----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
