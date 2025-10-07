import asyncio
import psutil
import logging
from config import MONITOR_INTERVAL, AUTO_RESTART, MAX_RESTART_ATTEMPTS

logger = logging.getLogger(__name__)

class BotMonitor:
    def __init__(self, db):
        self.db = db
    
    async def start_monitoring(self):
        """Start monitoring all deployed bots"""
        logger.info("🔍 Bot monitor started")
        
        while True:
            try:
                await self.check_all_bots()
            except Exception as e:
                logger.error(f"Monitor error: {e}")
            
            await asyncio.sleep(MONITOR_INTERVAL)
    
    async def check_all_bots(self):
        """Check status of all bots"""
        bots = await self.db.get_all_bots()
        
        for bot in bots:
            if bot.get('status') == 'running':
                await self.check_bot_health(bot)
    
    async def check_bot_health(self, bot):
        """Check if bot process is running"""
        pid = bot.get('pid')
        bot_id = str(bot['_id'])
        
        if not pid:
            return
        
        try:
            process = psutil.Process(pid)
            
            # Check if process exists
            if not process.is_running():
                logger.warning(f"Bot {bot_id} crashed!")
                await self.handle_crash(bot)
                return
            
            # Get resource usage
            cpu = process.cpu_percent(interval=0.1)
            ram = process.memory_info().rss / (1024 * 1024)  # MB
            
            # Update stats
            await self.db.update_bot_stats(bot_id, cpu, ram)
        
        except psutil.NoSuchProcess:
            logger.warning(f"Bot {bot_id} process not found!")
            await self.handle_crash(bot)
        except Exception as e:
            logger.error(f"Health check error for {bot_id}: {e}")
    
    async def handle_crash(self, bot):
        """Handle bot crash"""
        bot_id = str(bot['_id'])
        restart_count = bot.get('restart_count', 0)
        
        # Update status
        await self.db.update_bot_status(bot_id, 'crashed')
        
        # Auto-restart if enabled
        if AUTO_RESTART and restart_count < MAX_RESTART_ATTEMPTS:
            logger.info(f"Auto-restarting bot {bot_id} (attempt {restart_count + 1})")
            
            from utils.deployer import BotDeployer
            deployer = BotDeployer()
            
            result = await deployer.start_bot(bot_id)
            
            if result['success']:
                await self.db.update_bot(bot_id, {
                    'status': 'running',
                    'pid': result['pid'],
                    'restart_count': restart_count + 1
                })
                logger.info(f"Bot {bot_id} restarted successfully")
            else:
                logger.error(f"Failed to restart bot {bot_id}: {result.get('error')}")