import asyncio
import logging

from discord.ext import commands
from aiohttp import web

from config import DISCORD_BOT_TOKEN, REDIS_URL
from github_webhook import GitHubWebhookHandler
from disk_monitor import DiskMonitor
from event_listener import EventListener

logger = logging.getLogger(__name__)

# Create the Discord bot instance with a simple command prefix.
bot = commands.Bot(command_prefix="!")

async def start_webhook_server():
    """
    Starts the aiohttp server for GitHub webhooks.
    """
    app = web.Application()
    github_handler = GitHubWebhookHandler(bot)
    app.router.add_post("/github-webhook", github_handler.handle)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    logger.info("GitHub webhook server running on http://0.0.0.0:8080")

@bot.event
async def on_ready():
    logger.info("Bot logged in as %s", bot.user)
    # Start the GitHub webhook server
    asyncio.create_task(start_webhook_server())
    # Start the event listener for system events from Redis pub/sub
    event_listener = EventListener(bot, redis_url=REDIS_URL, channel_name="server_events")
    asyncio.create_task(event_listener.start())

def run_bot():
    """
    Runs the Discord bot.
    """
    bot.run(DISCORD_BOT_TOKEN)
