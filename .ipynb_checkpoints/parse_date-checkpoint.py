import asyncio
import json
import yaml
from datetime import datetime, timedelta
import re
from playwright.async_api import async_playwright


def parse_russian_date(time_label):
    """Parse Russian time labels to YYYY-MM-DD HH:MM:SS format"""
    if not time_label:
        return None
    
    now = datetime.now()
    months = {
        'янв': 1, 'фев': 2, 'мар': 3, 'апр': 4, 'май': 5, 'июн': 6,
        'июл': 7, 'авг': 8, 'сен': 9, 'окт': 10, 'ноя': 11, 'дек': 12
    }
    
    try:
        # Pattern 1: "сегодня, HH:MM"
        if 'сегодня' in time_label:
            match = re.search(r'(\d{1,2}):(\d{2})', time_label)
            if match:
                hour, minute = int(match.group(1)), int(match.group(2))
                result = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                return result.strftime('%Y-%m-%d %H:%M:%S')
        
        # Pattern 2: "вчера, HH:MM"
        elif 'вчера' in time_label:
            match = re.search(r'(\d{1,2}):(\d{2})', time_label)
            if match:
                hour, minute = int(match.group(1)), int(match.group(2))
                result = now - timedelta(days=1)
                result = result.replace(hour=hour, minute=minute, second=0, microsecond=0)
                return result.strftime('%Y-%m-%d %H:%M:%S')
        
        # Pattern 3: "DD месяц, HH:MM"
        else:
            match = re.search(r'(\d{1,2})\s+([а-яА-Я]+),?\s+(\d{1,2}):(\d{2})', time_label)
            if match:
                day = int(match.group(1))
                month_name = match.group(2).lower()
                hour = int(match.group(3))
                minute = int(match.group(4))
                
                if month_name in months:
                    month = months[month_name]
                    year = now.year
                    
                    result = datetime(year, month, day, hour, minute, 0)
                    
                    # If date is in future, it's from last year
                    if result > now:
                        result = result.replace(year=year - 1)
                    
                    return result.strftime('%Y-%m-%d %H:%M:%S')
    
    except Exception as e:
        print(f"Error parsing time label '{time_label}': {e}")
    
    return time_label  # Return original if parsing fails