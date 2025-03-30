import asyncio
import json
import logging

import redis.asyncio as aioredis
from discord.ext import commands
from config import LAB_CHANNEL_ID, REDIS_URL

logger = logging.getLogger(__name__)

class EventListener:
    def __init__(self, bot: commands.Bot, redis_url: str, channel_name: str):
        """
        :param bot: The Discord bot instance.
        :param redis_url: URL for connecting to Redis.
        :param channel_name: The Redis channel to subscribe to.
        """
        self.bot = bot
        self.redis_url = redis_url
        self.channel_name = channel_name
        self.redis = aioredis.from_url(redis_url)

    async def start(self):
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(self.channel_name)
        logger.info("Subscribed to Redis channel: %s", self.channel_name)
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=5.0)
            if message:
                try:
                    data = json.loads(message["data"])
                    await self.process_event(data)
                except Exception as e:
                    logger.exception("Error processing message from Redis: %s", e)
            await asyncio.sleep(0.1)

    async def process_event(self, data: dict):
        """
        Process the event received from the server.
        Expected data format:
            {
                "type": "system_error",  # or "backup", "disk_warning", etc.
                "message": "Detailed description of the event."
            }
        """
        await self.bot.wait_until_ready()
        lab_channel = self.bot.get_channel(LAB_CHANNEL_ID)
        if lab_channel is None:
            logger.error("Lab channel (ID: %s) not found", LAB_CHANNEL_ID)
            return

        event_type = data.get("type", "unknown")
        message = f"**System Event ({event_type})**: {data.get('message', 'No details provided')}"

        try:
            await lab_channel.send(message)
            logger.info("Sent system event alert: %s", message)
        except Exception as e:
            logger.exception("Failed to send system event alert: %s", e)
