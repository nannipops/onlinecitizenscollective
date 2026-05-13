from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive"

@app.route("/slack/events", methods=["POST"])
def slack_events():
    return "ok"

if __name__ == "__main__":
    app.run()
