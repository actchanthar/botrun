import os
from dotenv import load_dotenv

load_dotenv()

# Main Bot Configuration
API_ID = int(os.getenv("API_ID", "25465082"))
API_HASH = os.getenv("API_HASH", "4a6b5e40c8bc08c8af09add6cca23b18")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8320701136:AAHUXMQ6tgg23RO2elCt05M7xZ-aBZcJcB4")

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://act:actdata@cluster0.z6trhoh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DATABASE_NAME = os.getenv("DATABASE_NAME", "bot_manager")

# Admin Configuration
ADMINS = [int(x) for x in os.getenv("ADMINS", "").split(",") if x.strip()]

# Bot Deployment Settings
BOTS_DIR = os.path.join(os.getcwd(), "deployed_bots")
MAX_BOTS_FREE = int(os.getenv("MAX_BOTS_FREE", "2"))
MAX_BOTS_PREMIUM = int(os.getenv("MAX_BOTS_PREMIUM", "10"))

# Premium Plans (in seconds)
PREMIUM_PLANS = {
    "30days": 30 * 24 * 60 * 60,
    "90days": 90 * 24 * 60 * 60,
    "1year": 365 * 24 * 60 * 60
}

# System Monitoring
MONITOR_INTERVAL = 60  # Check bot status every 60 seconds
AUTO_RESTART = True
MAX_RESTART_ATTEMPTS = 3

# Notification Settings
PREMIUM_EXPIRY_WARNING_DAYS = 5