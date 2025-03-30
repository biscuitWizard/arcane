import json
import hmac
import hashlib
import asyncio
import logging

from aiohttp import web
from discord.ext import commands

from config import GITHUB_WEBHOOK_SECRET, GITHUB_CHANNEL_ID

logger = logging.getLogger(__name__)

class GitHubWebhookHandler:
    """
    Handles incoming GitHub webhook events and posts formatted messages to Discord.
    """
    def __init__(self, discord_bot: commands.Bot):
        self.bot = discord_bot

    async def handle(self, request: web.Request) -> web.Response:
        payload = await request.read()

        # Verify the webhook payload signature if a secret is provided
        signature = request.headers.get('X-Hub-Signature-256')
        if GITHUB_WEBHOOK_SECRET:
            if not signature:
                return web.Response(status=400, text="Missing signature")
            digest = hmac.new(GITHUB_WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
            expected_signature = f"sha256={digest}"
            if not hmac.compare_digest(expected_signature, signature):
                return web.Response(status=403, text="Signature mismatch")

        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return web.Response(status=400, text="Invalid JSON payload")

        # Determine the GitHub event type from headers
        event_type = request.headers.get("X-GitHub-Event", "unknown")
        # Process event asynchronously
        asyncio.create_task(self.process_event(event_type, data))
        return web.Response(status=200, text="OK")

    async def process_event(self, event_type: str, data: dict):
        # Wait until the bot is fully ready before sending messages
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(GITHUB_CHANNEL_ID)
        if channel is None:
            logger.error("GitHub channel (ID: %s) not found. Check your GITHUB_CHANNEL_ID.", GITHUB_CHANNEL_ID)
            return

        message = None
        if event_type == "push":
            ref = data.get("ref", "unknown ref")
            commits = data.get("commits", [])
            pusher = data.get("pusher", {}).get("name", "someone")
            commit_count = len(commits)
            commit_msgs = "\n".join([f"- {commit.get('message', '').strip()}" for commit in commits[:3]])
            more_text = f"\n...and {commit_count - 3} more commit(s)." if commit_count > 3 else ""
            message = f"**Push Event** by {pusher} on {ref}:\n{commit_msgs}{more_text}"

        elif event_type == "pull_request":
            action = data.get("action", "performed an action on")
            pr = data.get("pull_request", {})
            title = pr.get("title", "No title")
            url = pr.get("html_url", "")
            user = pr.get("user", {}).get("login", "someone")
            message = f"**Pull Request {action.capitalize()}** by {user}: [{title}]({url})"

        elif event_type == "issue_comment":
            action = data.get("action", "updated")
            issue = data.get("issue", {})
            comment = data.get("comment", {})
            issue_title = issue.get("title", "No title")
            url = comment.get("html_url", "")
            user = comment.get("user", {}).get("login", "someone")
            message = f"**Issue Comment {action.capitalize()}** by {user} on issue \"{issue_title}\": [View Comment]({url})"

        else:
            message = f"Received GitHub event: **{event_type}**"

        try:
            await channel.send(message)
            logger.info("Posted GitHub event '%s' to channel ID %s", event_type, GITHUB_CHANNEL_ID)
        except Exception as e:
            logger.exception("Failed to send message to Discord: %s", e)
