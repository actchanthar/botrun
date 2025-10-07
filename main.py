import asyncio
import logging
from pyrogram import Client, idle
from pyrogram.enums import ParseMode
from config import API_ID, API_HASH, BOT_TOKEN
from database.db import Database
from utils.monitor import BotMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Bot
app = Client(
    "bot_manager",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins"),
    parse_mode=ParseMode.MARKDOWN
)

# Global database instance
db = Database()

async def startup():
    """Startup tasks"""
    logger.info("🚀 Bot Manager Starting...")
    await db.connect()

    # Initialize bot monitor
    monitor = BotMonitor(db)
    asyncio.create_task(monitor.start_monitoring())

    # Check premium expiries
    asyncio.create_task(check_premium_expiry())

    logger.info("✅ Bot Manager Ready!")

async def check_premium_expiry():
    """Check and notify premium expiries"""
    from datetime import datetime, timedelta
    from config import PREMIUM_EXPIRY_WARNING_DAYS

    while True:
        try:
            users = await db.get_expiring_premium_users(PREMIUM_EXPIRY_WARNING_DAYS)
            for user in users:
                days_left = (user['premium_expiry'] - datetime.now()).days
                message_text = (
                    f"⚠️ **Premium Expiry Warning**

"
                    f"Your premium subscription expires in **{days_left} days**.
"
                    f"Renew now to continue using premium features!"
                )
                await app.send_message(user['user_id'], message_text)
                await db.mark_notified(user['user_id'])
        except Exception as e:
            logger.error(f"Premium expiry check error: {e}")

        await asyncio.sleep(3600)  # Check every hour

async def main():
    await app.start()
    await startup()
    await idle()
    await db.disconnect()
    await app.stop()

if __name__ == "__main__":
    asyncio.run(main())