from pyrogram import Client, filters
from pyrogram.types import Message
from main import db
from config import MAX_BOTS_FREE, MAX_BOTS_PREMIUM
from utils.deployer import BotDeployer
import re

deployer = BotDeployer()

# Bot token regex
TOKEN_PATTERN = re.compile(r'^d+:[A-Za-z0-9_-]{35}$')
GITHUB_PATTERN = re.compile(r'github.com/[w-]+/[w-]+')

@Client.on_message(filters.command("deploy") & filters.private)
async def deploy_command(client: Client, message: Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    if user.get('is_banned'):
        await message.reply_text("⛔ You are banned from using this bot.")
        return
    
    # Check bot limit
    is_premium = await db.is_premium(user_id)
    bot_count = await db.count_user_bots(user_id)
    max_bots = MAX_BOTS_PREMIUM if is_premium else MAX_BOTS_FREE
    
    if bot_count >= max_bots:
        await message.reply_text(
            f"❌ **Bot Limit Reached**

"
            f"You have {bot_count}/{max_bots} bots deployed.
"
            f"{'Upgrade to premium for more bots!' if not is_premium else 'Delete a bot to deploy a new one.'}"
        )
        return
    
    # Parse command
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply_text(
            "❌ **Invalid Command**

"
            "**Usage:**
"
            "`/deploy BOT_TOKEN`
"
            "`/deploy BOT_TOKEN Custom Name`

"
            "**Example:**
"
            "`/deploy 123456:ABC-DEF1234 My File Bot`"
        )
        return
    
    # Extract token and optional name
    parts = args[1].split(maxsplit=1)
    bot_token = parts[0]
    bot_name = parts[1] if len(parts) > 1 else None
    
    # Validate token
    if not TOKEN_PATTERN.match(bot_token):
        await message.reply_text("❌ Invalid bot token format!")
        return
    
    # Deploy bot
    status_msg = await message.reply_text("🚀 **Deploying your bot...**

Validating token...")
    
    try:
        result = await deployer.deploy_from_token(bot_token, user_id, bot_name)
        
        if result['success']:
            # Save to database
            bot_data = {
                "bot_id": result['bot_id'],
                "bot_username": result['bot_username'],
                "bot_name": result['bot_name'],
                "bot_token": bot_token,
                "pid": result['pid'],
                "deploy_method": "token"
            }
            db_id = await db.add_bot(user_id, bot_data)
            
            await status_msg.edit_text(
                f"✅ **Bot Deployed Successfully!**

"
                f"🤖 **Bot:** @{result['bot_username']}
"
                f"📝 **Name:** {result['bot_name']}
"
                f"🆔 **Bot ID:** `{db_id}`
"
                f"🟢 **Status:** Running

"
                f"Use /mybots to manage your bot."
            )
        else:
            await status_msg.edit_text(f"❌ **Deployment Failed**

{result['error']}")
    
    except Exception as e:
        await status_msg.edit_text(f"❌ **Error:** {str(e)}")

@Client.on_message(filters.command("deploy_github") & filters.private)
async def deploy_github_command(client: Client, message: Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    if user.get('is_banned'):
        await message.reply_text("⛔ You are banned.")
        return
    
    # Check bot limit
    is_premium = await db.is_premium(user_id)
    bot_count = await db.count_user_bots(user_id)
    max_bots = MAX_BOTS_PREMIUM if is_premium else MAX_BOTS_FREE
    
    if bot_count >= max_bots:
        await message.reply_text(f"❌ Bot limit reached ({bot_count}/{max_bots})")
        return
    
    # Parse command
    args = message.text.split()
    if len(args) < 3:
        await message.reply_text(
            "❌ **Invalid Command**

"
            "**Usage:**
"
            "`/deploy_github REPO_URL BOT_TOKEN`

"
            "**Example:**
"
            "`/deploy_github https://github.com/user/bot 123456:ABC-DEF`"
        )
        return
    
    repo_url = args[1]
    bot_token = args[2]
    bot_name = " ".join(args[3:]) if len(args) > 3 else None
    
    # Validate
    if not GITHUB_PATTERN.search(repo_url):
        await message.reply_text("❌ Invalid GitHub URL!")
        return
    
    if not TOKEN_PATTERN.match(bot_token):
        await message.reply_text("❌ Invalid bot token!")
        return
    
    # Deploy
    status_msg = await message.reply_text(
        "🚀 **Deploying from GitHub...**

"
        "📥 Cloning repository..."
    )
    
    try:
        result = await deployer.deploy_from_github(repo_url, bot_token, user_id, bot_name)
        
        if result['success']:
            bot_data = {
                "bot_id": result['bot_id'],
                "bot_username": result['bot_username'],
                "bot_name": result['bot_name'],
                "bot_token": bot_token,
                "pid": result['pid'],
                "deploy_method": "github",
                "repo_url": repo_url
            }
            db_id = await db.add_bot(user_id, bot_data)
            
            await status_msg.edit_text(
                f"✅ **Bot Deployed from GitHub!**

"
                f"🤖 **Bot:** @{result['bot_username']}
"
                f"📝 **Name:** {result['bot_name']}
"
                f"📦 **Repo:** {repo_url}
"
                f"🆔 **Bot ID:** `{db_id}`
"
                f"🟢 **Status:** Running"
            )
        else:
            await status_msg.edit_text(f"❌ **Deployment Failed**

{result['error']}")
    
    except Exception as e:
        await status_msg.edit_text(f"❌ **Error:** {str(e)}")