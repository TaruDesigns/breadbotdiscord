import os

from loguru import logger

from registry import REGISTRY

if __name__ == "__main__":
    logger.info("Startup: Creating DB")
    REGISTRY.db.create_db()
    logger.info("Startup: Creating Folders")
    os.makedirs(REGISTRY.settings.downloads_path, exist_ok=True)
    logger.info("Startup: Starting Bot")
    REGISTRY.bot.run(REGISTRY.settings.discord_token)
