from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from main import db
from datetime import datetime

def format_uptime(start_time):
    """Format uptime duration"""
    if not start_time:
        return "N/A"
    delta = datetime.now() - start_time
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    
    if days > 0:
        return f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

def get_status_emoji(status):
    """Get emoji for bot status"""
    status_map = {
        "running": "🟢",
        "stopped": "🔴",
        "restarting": "🟡",
        "crashed": "⚠️"
    }
    return status_map.get(status, "⚪")

@Client.on_message(filters.command("mybots") & filters.private)
async def mybots_command(client, message):
    user_id = message.from_user.id
    bots = await db.get_user_bots(user_id)
    
    if not bots:
        await message.reply_text(
            "📭 **No Bots Deployed**

"
            "Deploy your first bot with:
"
            "`/deploy YOUR_BOT_TOKEN`"
        )
        return
    
    text = "🤖 **YOUR BOTS STATUS:**

"
    
    keyboard = []
    for idx, bot in enumerate(bots, 1):
        status = bot.get('status', 'unknown')
        emoji = get_status_emoji(status)
        uptime = format_uptime(bot.get('uptime_start'))
        cpu = bot.get('cpu_usage', 0)
        ram = bot.get('ram_usage', 0)
        
        bot_name = bot.get('bot_name', 'Unknown')
        username = bot.get('bot_username', 'unknown')
        
        text += f"{idx}. **{bot_name}** {emoji} {status.upper()}
"
        text += f"   @{username}
"
        text += f"   ⏰ Uptime: {uptime}
"
        text += f"   📊 CPU: {cpu:.1f}% | RAM: {ram:.1f}MB

"
        
        # Add button for this bot
        bot_id = str(bot['_id'])
        keyboard.append([
            InlineKeyboardButton(
                f"{'🟢' if status == 'running' else '🔴'} {bot_name[:20]}",
                callback_data=f"bot_{bot_id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data="mybots_refresh")])
    
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))