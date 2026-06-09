# Print Notifications

Get a push when a print finishes, fails, or errors. This wires Moonraker's `[notifier]` to
[Apprise](https://github.com/caronc/apprise), which talks to roughly a hundred services through one
address format.

## Setup

1. Pick a service and get its Apprise URL. Common ones:
   - **ntfy** (free, no account): `ntfy://ntfy.sh/your-topic-name`
   - **Telegram**: `tgram://{bot_token}/{chat_id}`
   - **Discord**: `discord://{webhook_id}/{webhook_token}`
   - **Pushover**: `pover://{user_key}@{token}`
   Full list and formats: github.com/caronc/apprise.
2. Paste it into **Apprise URL**, choose which events to be notified on, and install.

You can install more than one notifier (give each a different name) to reach several destinations.

## How the dependency works

Apprise is pure-Python. It is baked into this package at build time and linked into Moonraker's
interpreter when you install; the printer never runs `pip` (ADR-0036).
