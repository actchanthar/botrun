from datetime import datetime

def format_bytes(bytes_value):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} TB"

def format_duration(seconds):
    """Format duration in seconds to human readable format"""
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    
    if days > 0:
        return f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

def get_expiry_text(expiry_date):
    """Get human readable expiry text"""
    if not expiry_date:
        return "Never"
    
    delta = expiry_date - datetime.now()
    if delta.total_seconds() < 0:
        return "Expired"
    
    days = delta.days
    if days == 0:
        hours = delta.seconds // 3600
        return f"{hours} hours"
    elif days == 1:
        return "1 day"
    else:
        return f"{days} days"