from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from main import db
from datetime import datetime

@Client.on_message(filters.command("premium") & filters.private)
async def premium_command(client, message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    is_premium = await db.is_premium(user_id)
    
    if is_premium:
        expiry = user.get('premium_expiry')
        days_left = (expiry - datetime.now()).days if expiry else 0
        
        text = f"""
💎 **Premium Status: ACTIVE**

⏰ **Expires:** {expiry.strftime('%Y-%m-%d %H:%M')}
📅 **Days Remaining:** {days_left} days

**Premium Benefits:**
✅ Deploy up to 10 bots
✅ Auto-restart on crash
✅ Priority support
✅ Advanced monitoring
✅ GitHub deployment

Want to extend? Contact: @YourSupportUsername
"""
    else:
        text = """
💎 **Upgrade to Premium**

**Free Plan:**
• Max 2 bots
• Basic features

**Premium Plans:**

**30 Days - $5**
• 10 bots
• Auto-restart
• Priority support

**90 Days - $12** (20% OFF)
• All premium features
• Best value for 3 months

**1 Year - $40** (33% OFF)
• All premium features
• Maximum savings

📞 **To Purchase:**
Contact: @YourSupportUsername
Payment: Send screenshot after payment
"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Purchase Premium", url="https://t.me/YourSupportUsername")]
    ])
    
    await message.reply_text(text, reply_markup=keyboard)