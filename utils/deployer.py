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
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            # Wait a bit to check if it started
            await asyncio.sleep(2)
            
            if process.poll() is None:
                return {
                    'success': True,
                    'bot_id': bot_id,
                    'bot_username': username,
                    'bot_name': bot_name,
                    'pid': process.pid,
                    'bot_dir': bot_dir
                }
            else:
                return {'success': False, 'error': 'Bot process failed to start'}
        
        except Exception as e:
            logger.error(f"Deployment error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def deploy_from_github(self, repo_url, bot_token, user_id, custom_name=None):
        """Deploy bot from GitHub repository"""
        from git import Repo
        
        # Validate token first
        validation = await self.validate_token(bot_token)
        if not validation['valid']:
            return {'success': False, 'error': validation['error']}
        
        bot_id = validation['bot_id']
        username = validation['username']
        bot_name = custom_name or validation['first_name']
        
        # Create bot directory
        bot_dir = os.path.join(BOTS_DIR, f"user_{user_id}_bot_{bot_id}_github")
        
        try:
            # Clone repository
            Repo.clone_from(repo_url, bot_dir)
            
            # Create .env file with token
            env_file = os.path.join(bot_dir, ".env")
            with open(env_file, "w") as f:
                f.write(f"BOT_TOKEN={bot_token}
")
            
            # Install requirements
            req_file = os.path.join(bot_dir, "requirements.txt")
            if os.path.exists(req_file):
                subprocess.run(["pip3", "install", "-r", req_file], cwd=bot_dir)
            
            # Find main file (main.py or bot.py)
            main_file = None
            for filename in ["main.py", "bot.py", "run.py"]:
                path = os.path.join(bot_dir, filename)
                if os.path.exists(path):
                    main_file = path
                    break
            
            if not main_file:
                return {'success': False, 'error': 'No main file found (main.py, bot.py, or run.py)'}
            
            # Start bot
            process = subprocess.Popen(
                ["python3", os.path.basename(main_file)],
                cwd=bot_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            await asyncio.sleep(2)
            
            if process.poll() is None:
                return {
                    'success': True,
                    'bot_id': bot_id,
                    'bot_username': username,
                    'bot_name': bot_name,
                    'pid': process.pid,
                    'bot_dir': bot_dir
                }
            else:
                return {'success': False, 'error': 'Bot failed to start'}
        
        except Exception as e:
            logger.error(f"GitHub deployment error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def start_bot(self, bot_id):
        """Start a stopped bot"""
        from main import db
        bot = await db.get_bot(bot_id)
        
        if not bot:
            return {'success': False, 'error': 'Bot not found'}
        
        bot_dir = bot.get('bot_dir')
        if not bot_dir or not os.path.exists(bot_dir):
            return {'success': False, 'error': 'Bot directory not found'}
        
        # Find bot file
        bot_file = os.path.join(bot_dir, "bot.py")
        if not os.path.exists(bot_file):
            # Try main.py for GitHub bots
            bot_file = os.path.join(bot_dir, "main.py")
            if not os.path.exists(bot_file):
                return {'success': False, 'error': 'Bot file not found'}
        
        try:
            process = subprocess.Popen(
                ["python3", os.path.basename(bot_file)],
                cwd=bot_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            await asyncio.sleep(1)
            
            if process.poll() is None:
                return {'success': True, 'pid': process.pid}
            else:
                return {'success': False, 'error': 'Failed to start'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def stop_bot(self, bot_id):
        """Stop a running bot"""
        from main import db
        bot = await db.get_bot(bot_id)
        
        if not bot:
            return {'success': False, 'error': 'Bot not found'}
        
        pid = bot.get('pid')
        if not pid:
            return {'success': False, 'error': 'No PID found'}
        
        try:
            process = psutil.Process(pid)
            process.terminate()
            process.wait(timeout=5)
            return {'success': True}
        except psutil.NoSuchProcess:
            return {'success': True, 'message': 'Process already stopped'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def restart_bot(self, bot_id):
        """Restart a bot"""
        stop_result = await self.stop_bot(bot_id)
        await asyncio.sleep(1)
        return await self.start_bot(bot_id)