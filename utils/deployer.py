import os
import asyncio
import subprocess
import psutil
import aiohttp
from pathlib import Path
from config import BOTS_DIR
import logging

logger = logging.getLogger(__name__)

class BotDeployer:
    def __init__(self):
        # Create bots directory
        Path(BOTS_DIR).mkdir(exist_ok=True)
    
    async def validate_token(self, token):
        """Validate bot token and get bot info"""
        async with aiohttp.ClientSession() as session:
            try:
                url = f"https://api.telegram.org/bot{token}/getMe"
                async with session.get(url) as response:
                    data = await response.json()
                    if data.get('ok'):
                        bot_info = data['result']
                        return {
                            'valid': True,
                            'bot_id': bot_info['id'],
                            'username': bot_info['username'],
                            'first_name': bot_info.get('first_name', 'Bot')
                        }
                    return {'valid': False, 'error': 'Invalid token'}
            except Exception as e:
                return {'valid': False, 'error': str(e)}
    
    async def deploy_from_token(self, bot_token, user_id, custom_name=None):
        """Deploy a simple echo bot from token"""
        # Validate token
        validation = await self.validate_token(bot_token)
        if not validation['valid']:
            return {'success': False, 'error': validation['error']}
        
        bot_id = validation['bot_id']
        username = validation['username']
        bot_name = custom_name or validation['first_name']
        
        # Create bot directory
        bot_dir = os.path.join(BOTS_DIR, f"user_{user_id}_bot_{bot_id}")
        os.makedirs(bot_dir, exist_ok=True)
        
        # Create simple bot script
        bot_script = f"""
import logging
from pyrogram import Client, filters

logging.basicConfig(level=logging.INFO)

app = Client(
    "deployed_bot_{bot_id}",
    bot_token="{bot_token}",
    workdir="{bot_dir}"
)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        f"👋 Hello! I'm **{bot_name}**\
\
"
        "I'm deployed via Bot Manager.\
"
        "Send me any message and I'll echo it back!"
    )

@app.on_message(filters.text & filters.private)
async def echo(client, message):
    await message.reply_text(f"You said: {{message.text}}")

if __name__ == "__main__":
    app.run()
"""
        
        bot_file = os.path.join(bot_dir, "bot.py")
        with open(bot_file, "w") as f:
            f.write(bot_script)
        
        # Start bot process
        try:
            process = subprocess.Popen(
                ["python3", bot_file],
                cwd=bot_dir,
                stdout