from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from main import db
from config import ADMINS

@Client.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # Add user to database
    await db.add_user(user_id, username, first_name)
    user = await db.get_user(user_id)
    
    if user.get('is_banned'):
        await message.reply_text("⛔ You are banned from using this bot.")
        return
    
    is_premium = await db.is_premium(user_id)
    bot_count = await db.count_user_bots(user_id)
    
    welcome_text = f"""
👋 **Welcome to Bot Manager!**

Deploy and manage multiple Telegram bots from one place.

**Your Status:**
{'💎 Premium User' if is_premium else '🆓 Free User'}
🤖 Active Bots: {bot_count}

**Available Commands:**
/deploy - Deploy a new bot
/mybots - View your bots
/premium - View premium plans
/help - Get help

{'**Admin Commands:**
/admin - Admin panel' if user_id in ADMINS else ''}
"""
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🚀 Deploy Bot", callback_data="deploy"),
            InlineKeyboardButton("🤖 My Bots", callback_data="mybots")
        ],
        [
            InlineKeyboardButton("💎 Premium", callback_data="premium"),
            InlineKeyboardButton("❓ Help", callback_data="help")
        ]
    ])
    
    await message.reply_text(welcome_text, reply_markup=keyboard)

@Client.on_message(filters.command("help") & filters.private)
async def help_command(client, message):
    help_text = """
📖 **Bot Manager Help**

**Deployment Methods:**
1. **From Bot Token:**
   `/deploy YOUR_BOT_TOKEN`
   Example: `/deploy 123456:ABC-DEF1234ghIkl-zyx`

2. **From GitHub Repository:**
   `/deploy_github REPO_URL BOT_TOKEN`
   Example: `/deploy_github https://github.com/user/bot 123456:ABC-DEF`

**Bot Management:**
• `/mybots` - View all your bots
• Tap on a bot to see options (Start/Stop/Restart/Delete)
• Real-time status monitoring

**Premium Features:**
• Deploy up to 10 bots (vs 2 for free)
• Priority support
• Auto-restart on crash
• Advanced monitoring

**Need Help?**
Contact: @YourSupportUsername
"""
    await message.reply_text(help_text)