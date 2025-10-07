from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from main import db
from utils.deployer import BotDeployer

deployer = BotDeployer()

@Client.on_callback_query()
async def callback_handler(client: Client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id
    
    # Main menu callbacks
    if data == "deploy":
        await query.message.edit_text(
            "🚀 **Deploy a New Bot**

"
            "**Method 1: From Bot Token**
"
            "`/deploy YOUR_BOT_TOKEN`

"
            "**Method 2: From GitHub**
"
            "`/deploy_github REPO_URL BOT_TOKEN`"
        )
    
    elif data == "mybots":
        # Redirect to /mybots command
        await query.message.reply_text("/mybots")
    
    elif data == "premium":
        await query.message.reply_text("/premium")
    
    elif data == "help":
        await query.message.reply_text("/help")
    
    # Bot management callbacks
    elif data.startswith("bot_"):
        bot_id = data.split("_", 1)[1]
        bot = await db.get_bot(bot_id)
        
        if not bot or bot['user_id'] != user_id:
            await query.answer("❌ Bot not found!", show_alert=True)
            return
        
        status = bot.get('status', 'unknown')
        bot_name = bot.get('bot_name', 'Unknown')
        username = bot.get('bot_username', 'unknown')
        
        keyboard = []
        
        if status == "running":
            keyboard.append([
                InlineKeyboardButton("⏹️ Stop", callback_data=f"stop_{bot_id}"),
                InlineKeyboardButton("🔄 Restart", callback_data=f"restart_{bot_id}")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("▶️ Start", callback_data=f"start_{bot_id}")
            ])
        
        keyboard.append([
            InlineKeyboardButton("📊 Stats", callback_data=f"stats_{bot_id}"),
            InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_{bot_id}")
        ])
        keyboard.append([InlineKeyboardButton("◀️ Back", callback_data="mybots_refresh")])
        
        await query.message.edit_text(
            f"🤖 **Bot Management**

"
            f"**Name:** {bot_name}
"
            f"**Username:** @{username}
"
            f"**Status:** {status.upper()}
"
            f"**Bot ID:** `{bot_id}`",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    # Bot action callbacks
    elif data.startswith("start_"):
        bot_id = data.split("_", 1)[1]
        await query.answer("⏳ Starting bot...", show_alert=False)
        
        result = await deployer.start_bot(bot_id)
        if result['success']:
            await db.update_bot_status(bot_id, "running", result.get('pid'))
            await query.answer("✅ Bot started!", show_alert=True)
        else:
            await query.answer(f"❌ {result['error']}", show_alert=True)
        
        # Refresh view
        await callback_handler(client, CallbackQuery(data=f"bot_{bot_id}", from_user=query.from_user, message=query.message))
    
    elif data.startswith("stop_"):
        bot_id = data.split("_", 1)[1]
        await query.answer("⏳ Stopping bot...", show_alert=False)
        
        result = await deployer.stop_bot(bot_id)
        if result['success']:
            await db.update_bot_status(bot_id, "stopped")
            await query.answer("✅ Bot stopped!", show_alert=True)
        else:
            await query.answer(f"❌ {result['error']}", show_alert=True)
        
        await callback_handler(client, CallbackQuery(data=f"bot_{bot_id}", from_user=query.from_user, message=query.message))
    
    elif data.startswith("restart_"):
        bot_id = data.split("_", 1)[1]
        await query.answer("⏳ Restarting bot...", show_alert=False)
        
        result = await deployer.restart_bot(bot_id)
        if result['success']:
            await db.update_bot_status(bot_id, "running", result.get('pid'))
            await query.answer("✅ Bot restarted!", show_alert=True)
        else:
            await query.answer(f"❌ {result['error']}", show_alert=True)
        
        await callback_handler(client, CallbackQuery(data=f"bot_{bot_id}", from_user=query.from_user, message=query.message))
    
    elif data.startswith("delete_"):
        bot_id = data.split("_", 1)[1]
        
        # Confirmation keyboard
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Yes, Delete", callback_data=f"confirm_delete_{bot_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"bot_{bot_id}")
            ]
        ])
        
        await query.message.edit_text(
            "⚠️ **Confirm Deletion**

"
            "Are you sure you want to delete this bot?
"
            "This action cannot be undone!",
            reply_markup=keyboard
        )
    
    elif data.startswith("confirm_delete_"):
        bot_id = data.split("_", 2)[2]
        
        # Stop bot first
        await deployer.stop_bot(bot_id)
        
        # Delete from database
        deleted = await db.delete_bot(bot_id, user_id)
        
        if deleted:
            await query.answer("✅ Bot deleted!", show_alert=True)
            await query.message.edit_text(
                "✅ **Bot Deleted Successfully**

"
                "Use /mybots to view your remaining bots."
            )
        else:
            await query.answer("❌ Failed to delete bot!", show_alert=True)
    
    elif data == "mybots_refresh":
        # Refresh mybots list
        await query.message.reply_text("/mybots")
        await query.message.delete()