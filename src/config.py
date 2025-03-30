import os

# Discord configuration
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
if not DISCORD_BOT_TOKEN:
    raise EnvironmentError("DISCORD_BOT_TOKEN environment variable not set.")

# The numeric channel IDs
GITHUB_CHANNEL_ID = int(os.environ.get("GITHUB_CHANNEL_ID", "0"))
if GITHUB_CHANNEL_ID == 0:
    raise EnvironmentError("GITHUB_CHANNEL_ID environment variable not set or invalid.")

LAB_CHANNEL_ID = int(os.environ.get("LAB_CHANNEL_ID", "0"))
if LAB_CHANNEL_ID == 0:
    raise EnvironmentError("LAB_CHANNEL_ID environment variable not set or invalid.")

# GitHub webhook secret (optional)
GITHUB_WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET", "")