import os
from slack_sdk import WebClient

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
CHANNEL_ID = os.environ["SLACK_CHANNEL_ID"]

client = WebClient(token=SLACK_BOT_TOKEN)

# -----------------------------
# Example tracked data
# Replace with database later
# -----------------------------
POSTS = [
    {
        "url": "https://instagram.com/p/abc123",
        "platform": "Instagram",
        "volunteer_engagement": {
            "likes": 25,
            "comments": 10,
            "shares": 7
        }
    },
    {
        "url": "https://x.com/post/xyz456",
        "platform": "X",
        "volunteer_engagement": {
            "likes": 18,
            "comments": 4,
            "shares": 12
        }
    }
]

# -----------------------------
# Platform totals (mock or API)
# -----------------------------
def get_platform_totals(post_url):
    return {
        "likes": 400,
        "comments": 35,
        "shares": 12
    }

# -----------------------------
# Build report
# -----------------------------
def build_report():
    report_lines = []

    total = {
        "likes": 0,
        "comments": 0,
        "shares": 0
    }

    volunteer_total = {
        "likes": 0,
        "comments": 0,
        "shares": 0
    }

    for post in POSTS:
        totals = get_platform_totals(post["url"])
        v = post["volunteer_engagement"]

        # aggregate totals
        for k in total:
            total[k] += totals[k]
            volunteer_total[k] += v[k]

        line = (
            f"*{post['platform']}*\n"
            f"{post['url']}\n\n"
            f"📊 Total: ❤️ {totals['likes']} | 💬 {totals['comments']} | 🔁 {totals['shares']}\n"
            f"👥 Volunteers: ❤️ {v['likes']} | 💬 {v['comments']} | 🔁 {v['shares']}\n"
        )

        report_lines.append(line)

    def pct(v, t):
        return round((v / t) * 100, 1) if t else 0

    footer = (
        "\n💪 *Daily Volunteer Impact Summary*\n"
        f"❤️ Likes: {volunteer_total['likes']} ({pct(volunteer_total['likes'], total['likes'])}%)\n"
        f"💬 Comments: {volunteer_total['comments']} ({pct(volunteer_total['comments'], total['comments'])}%)\n"
        f"🔁 Shares: {volunteer_total['shares']} ({pct(volunteer_total['shares'], total['shares'])}%)\n"
    )

    return "\n\n".join(report_lines) + footer

# -----------------------------
# Send to Slack
# -----------------------------
def send_to_slack(message):
    client.chat_postMessage(
        channel=CHANNEL_ID,
        text=message
    )

if __name__ == "__main__":
    report = build_report()
    send_to_slack(report)
