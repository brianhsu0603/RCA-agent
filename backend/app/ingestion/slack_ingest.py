"""Pulls recent messages from configured Slack channels into the slack_messages table.

This is the real-data counterpart to the mock rows loaded by seed.py. It's not run
automatically (no live workspace is configured in this scaffold) - wire it up as a
periodic job (cron / Celery beat) once SLACK_BOT_TOKEN and CHANNELS are set.

Requires bot scopes: channels:history, channels:read (and groups:history for private
channels). Run manually with: python -m app.ingestion.slack_ingest
"""

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from app.config import settings
from app.db import SessionLocal
from app.models import SlackMessage

CHANNELS = ["line3-fct2", "test-eng", "rf-cal"]


def ingest_channel(client: WebClient, channel_name: str, db) -> int:
    resolved = client.conversations_list(limit=200)
    channel_id = next(
        (c["id"] for c in resolved["channels"] if c["name"] == channel_name), None
    )
    if channel_id is None:
        print(f"channel #{channel_name} not found or bot not invited")
        return 0

    history = client.conversations_history(channel=channel_id, limit=200)
    inserted = 0
    for msg in history["messages"]:
        ts = msg.get("ts", "")
        exists = (
            db.query(SlackMessage)
            .filter(SlackMessage.channel == f"#{channel_name}", SlackMessage.ts == ts)
            .first()
        )
        if exists:
            continue
        db.add(
            SlackMessage(
                channel=f"#{channel_name}",
                thread_ts=msg.get("thread_ts", ts),
                author=msg.get("user", "unknown"),
                text=msg.get("text", ""),
                ts=ts,
            )
        )
        inserted += 1
    return inserted


def main() -> None:
    if not settings.slack_bot_token:
        print("SLACK_BOT_TOKEN not set - nothing to do. Mock Slack data is already seeded.")
        return

    client = WebClient(token=settings.slack_bot_token)
    db = SessionLocal()
    try:
        total = 0
        for channel in CHANNELS:
            try:
                total += ingest_channel(client, channel, db)
            except SlackApiError as e:
                print(f"Slack API error on #{channel}: {e.response['error']}")
        db.commit()
        print(f"Ingested {total} new Slack messages.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
