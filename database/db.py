from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
from config import MONGO_URI, DATABASE_NAME
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(MONGO_URI)
            self.db = self.client[DATABASE_NAME]
            
            # Create indexes
            await self.db.users.create_index("user_id", unique=True)
            await self.db.bots.create_index([("user_id", 1), ("bot_id", 1)])
            
            logger.info("✅ Connected to MongoDB")
        except Exception as e:
            logger.error(f"MongoDB connection error: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    # ========== USER MANAGEMENT ==========
    
    async def add_user(self, user_id, username=None, first_name=None):
        """Add new user to database"""
        user_data = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "joined_date": datetime.now(),
            "is_premium": False,
            "premium_expiry": None,
            "total_bots": 0,
            "is_banned": False,
            "notified": False
        }
        await self.db.users.update_one(
            {"user_id": user_id},
            {"$setOnInsert": user_data},
            upsert=True
        )
    
    async def get_user(self, user_id):
        """Get user from database"""
        return await self.db.users.find_one({"user_id": user_id})
    
    async def update_user(self, user_id, update_data):
        """Update user data"""
        await self.db.users.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
    
    async def is_premium(self, user_id):
        """Check if user has active premium"""
        user = await self.get_user(user_id)
        if not user or not user.get('is_premium'):
            return False
        
        expiry = user.get('premium_expiry')
        if expiry and expiry > datetime.now():
            return True
        
        # Premium expired, update status
        await self.update_user(user_id, {"is_premium": False})
        return False
    
    async def add_premium(self, user_id, days):
        """Add premium subscription"""
        expiry_date = datetime.now() + timedelta(days=days)
        await self.update_user(user_id, {
            "is_premium": True,
            "premium_expiry": expiry_date,
            "notified": False
        })
    
    async def get_all_users(self):
        """Get all users (admin)"""
        cursor = self.db.users.find({})
        return await cursor.to_list(length=None)
    
    async def get_expiring_premium_users(self, days_threshold):
        """Get users whose premium expires soon"""
        threshold_date = datetime.now() + timedelta(days=days_threshold)
        cursor = self.db.users.find({
            "is_premium": True,
            "premium_expiry": {"$lte": threshold_date, "$gte": datetime.now()},
            "notified": False
        })
        return await cursor.to_list(length=None)
    
    async def mark_notified(self, user_id):
        """Mark user as notified about premium expiry"""
        await self.update_user(user_id, {"notified": True})
    
    # ========== BOT MANAGEMENT ==========
    
    async def add_bot(self, user_id, bot_data):
        """Add deployed bot to database"""
        bot_data.update({
            "user_id": user_id,
            "deployed_at": datetime.now(),
            "status": "running",
            "uptime_start": datetime.now(),
            "restart_count": 0,
            "last_restart": None,
            "cpu_usage": 0.0,
            "ram_usage": 0.0
        })
        result = await self.db.bots.insert_one(bot_data)
        
        # Update user's total bots count
        await self.db.users.update_one(
            {"user_id": user_id},
            {"$inc": {"total_bots": 1}}
        )
        
        return str(result.inserted_id)
    
    async def get_bot(self, bot_id):
        """Get bot by ID"""
        from bson import ObjectId
        return await self.db.bots.find_one({"_id": ObjectId(bot_id)})
    
    async def get_user_bots(self, user_id):
        """Get all bots for a user"""
        cursor = self.db.bots.find({"user_id": user_id})
        return await cursor.to_list(length=None)
    
    async def get_all_bots(self):
        """Get all bots (admin)"""
        cursor = self.db.bots.find({})
        return await cursor.to_list(length=None)
    
    async def update_bot(self, bot_id, update_data):
        """Update bot data"""
        from bson import ObjectId
        await self.db.bots.update_one(
            {"_id": ObjectId(bot_id)},
            {"$set": update_data}
        )
    
    async def delete_bot(self, bot_id, user_id):
        """Delete bot from database"""
        from bson import ObjectId
        result = await self.db.bots.delete_one({
            "_id": ObjectId(bot_id),
            "user_id": user_id
        })
        
        if result.deleted_count > 0:
            await self.db.users.update_one(
                {"user_id": user_id},
                {"$inc": {"total_bots": -1}}
            )
        
        return result.deleted_count > 0
    
    async def count_user_bots(self, user_id):
        """Count user's bots"""
        return await self.db.bots.count_documents({"user_id": user_id})
    
    async def update_bot_status(self, bot_id, status, pid=None):
        """Update bot status"""
        update_data = {"status": status}
        if pid:
            update_data["pid"] = pid
        if status == "running":
            update_data["uptime_start"] = datetime.now()
        await self.update_bot(bot_id, update_data)
    
    async def update_bot_stats(self, bot_id, cpu, ram):
        """Update bot resource usage"""
        await self.update_bot(bot_id, {
            "cpu_usage": cpu,
            "ram_usage": ram
        })