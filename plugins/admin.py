from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from main import db
from config import ADMINS
import psutil
from datetime import datetime

def is_admin(user_id):
    return user_id in ADMINS

@Client.on_message(filters.command("admin") & filters.private & filters.user(ADMINS))
async def admin_panel(client, message):
    # Get statistics
    total_users = len(await db.get_all_users())
    total_bots = len(await db.get_all_bots())
    premium_users = len([u for u in await db.get_all_users() if u.get('is_premium')])
    
    # System stats
    cpu_percent = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    text = f"""
👑 **ADMIN PANEL**

**Bot Statistics:**
👥 Total Users: {total_users}
🤖 Total Bots: {total_bots}
💎 Premium Users: {premium_users}

**Server Resources:**
🖥️ CPU: {cpu_percent}%
💾 RAM: {ram.percent}% ({ram.used // (1024**3)}GB / {ram.total // (1024**3)}GB)
💿 Disk: {disk.percent}% ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)

**Admin Commands:**
/stats - Detailed statistics
/users - View all users
/allbots - View all deployed bots
/addpremium - Add premium to user
/ban - Ban a user
/unban - Unban a user
/broadcast - Send message to all users
"""
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
            InlineKeyboardButton("👥 Users", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton("🤖 All Bots", callback_data="admin_bots"),
            InlineKeyboardButton("🔄 Refresh", callback_data="admin_refresh")
        ]
    ])
    
    await message.reply_text(text, reply_markup=keyboard)

@Client.on_message(filters.command("addpremium") & filters.private & filters.user(ADMINS))
async def add_premium_command(client, message):
    args = message.text.split()
    if len(args) < 3:
        await message.reply_text(
            "**Usage:** `/addpremium USER_ID DAYS`
"
            "**Example:** `/addpremium 123456789 30`"
        )
        return
    
    try:
        user_id = int(args[1])
        days = int(args[2])
        
        await db.add_premium(user_id, days)
        await message.reply_text(f"✅ Added {days} days premium to user {user_id}")
        
        # Notify user
        try:
            await client.send_message(
                user_id,
                f"🎉 **Premium Activated!**

"
                f"You've been granted {days} days of premium access.
"
                f"Enjoy all premium features!"
            )
        except:
            pass
    except ValueError:
        await message.reply_text("❌ Invalid user ID or days!")

@Client.on_message(filters.command("ban") & filters.private & filters.user(ADMINS))
async def ban_command(client, message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("**Usage:** `/ban USER_ID`")
        return
    
    try:
        user_id = int(args[1])
        await db.update_user(user_id, {"is_banned": True})
        await message.reply_text(f"✅ Banned user {user_id}")
    except ValueError:
        await message.reply_text("❌ Invalid user ID!")

@Client.on_message(filters.command("unban") & filters.private & filters.user(ADMINS))
async def unban_command(client, message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("**Usage:** `/unban USER_ID`")
        return
    
    try:
        user_id = int(args[1])
        await db.update_user(user_id, {"is_banned": False})
        await message.reply_text(f"✅ Unbanned user {user_id}")
    except ValueError:
        await message.reply_text("❌ Invalid user ID!")

@Client.on_message(filters.command("broadcast") & filters.private & filters.user(ADMINS))
async def broadcast_command(client, message):
    if not message.reply_to_message:
        await message.reply_text("❌ Reply to a message to broadcast it!")
        return
    
    users = await db.get_all_users()
    success = 0
    failed = 0
    
    status_msg = await message.reply_text(f"📤 Broadcasting to {len(users)} users...")
    
    for user in users:
        try:
            await message.reply_to_message.copy(user['user_id'])
            success += 1
        except:
            failed += 1
    
    await status_msg.edit_text(
        f"✅ **Broadcast Complete**

"
        f"✅ Success: {success}
"
        f"❌ Failed: {failed}"
    )