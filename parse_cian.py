import asyncio
import json
import yaml
import os
from datetime import datetime, timedelta
import re
from playwright.async_api import async_playwright
from helpers import parse_russian_date
from telegram_bot import TelegramBot


def load_previous_data():
    """Load previous run data if exists"""
    if os.path.exists('parsed_data.json'):
        try:
            with open('parsed_data.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def track_changes(current_data):
    """Compare current data with previous run to detect changes"""
    previous_data = load_previous_data()
    
    # Create lookup dictionaries
    previous_offers = {item['offer_id']: item for item in previous_data}
    current_offers = {item['offer_id']: item for item in current_data}
    
    # Find new offers
    new_offers = []
    for offer_id, offer in current_offers.items():
        if offer_id not in previous_offers:
            new_offers.append(offer)
    
    # Find removed offers
    removed_offers = []
    for offer_id, offer in previous_offers.items():
        if offer_id not in current_offers:
            removed_offers.append(offer)
    
    # Find price changes
    price_changes = []
    for offer_id, current_offer in current_offers.items():
        if offer_id in previous_offers:
            previous_offer = previous_offers[offer_id]
            if (current_offer.get('price') != previous_offer.get('price') and 
                current_offer.get('price') is not None and 
                previous_offer.get('price') is not None):
                price_changes.append({
                    'offer': current_offer,
                    'old_price': previous_offer['price'],
                    'new_price': current_offer['price'],
                    'price_diff': current_offer['price'] - previous_offer['price']
                })
    
    return {
        'new_offers': new_offers,
        'removed_offers': removed_offers,
        'price_changes': price_changes
    }


def show_changes(changes):
    """Display detailed information about changes"""
    if changes['new_offers']:
        print(f"\n🆕 NEW OFFERS ({len(changes['new_offers'])}):")
        for offer in changes['new_offers']:
            price_str = f"{offer['price']:,} ₽" if offer['price'] else "Price not specified"
            metro_str = f" • {offer['metro_station']}" if offer['metro_station'] else ""
            print(f"  • {offer['offer_id']}: {price_str}{metro_str}")
            if offer['title']:
                print(f"    {offer['title'][:80]}...")
    
    if changes['price_changes']:
        print(f"\n💰 PRICE CHANGES ({len(changes['price_changes'])}):")
        for change in changes['price_changes']:
            offer = change['offer']
            old_price = f"{change['old_price']:,} ₽"
            new_price = f"{change['new_price']:,} ₽"
            diff = change['price_diff']
            direction = "📈" if diff > 0 else "📉"
            diff_str = f"{abs(diff):,} ₽"
            metro_str = f" • {offer['metro_station']}" if offer['metro_station'] else ""
            print(f"  • {offer['offer_id']}: {old_price} → {new_price} ({direction} {diff_str}){metro_str}")
    
    if changes['removed_offers']:
        print(f"\n❌ REMOVED OFFERS ({len(changes['removed_offers'])}):")
        for offer in changes['removed_offers']:
            price_str = f"{offer['price']:,} ₽" if offer['price'] else "Price not specified"
            metro_str = f" • {offer['metro_station']}" if offer['metro_station'] else ""
            print(f"  • {offer['offer_id']}: {price_str}{metro_str}")




async def parse_cian():
    # Read URLs from file
    with open('url.txt', 'r') as f:
        urls = [line.strip() for line in f.readlines() if line.strip() and line.strip().startswith('http')]
    
    # Read scripts from YAML file
    with open('scripts.yaml', 'r') as f:
        scripts = yaml.safe_load(f)
    
    primary_script = scripts['primary_script']
    wait_for_function = scripts['wait_for_function']
    
    async def parse_single_url(context, url, index):
        print(f"\nParsing URL {index+1}/{len(urls)}: {url[:80]}...")
        
        page = await context.new_page()
        
        try:
            # Navigate to URL
            await page.goto(url, wait_until='domcontentloaded', timeout=15000)
            
            # Wait for content to load using the wait function
            await page.wait_for_function(wait_for_function, timeout=10000)
            
            # Execute the primary script to extract data
            data = await page.evaluate(primary_script)
            
            # Process dates in Python
            for item in data:
                if 'time_label' in item and item['time_label']:
                    item['time_label'] = parse_russian_date(item['time_label'])
            
            print(f"Found {len(data)} offers on URL {index+1}")
            return data
            
        finally:
            await page.close()
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        try:
            # Process all URLs in parallel
            tasks = [parse_single_url(context, url, i) for i, url in enumerate(urls)]
            results = await asyncio.gather(*tasks)
            
            # Combine all results
            all_data = []
            for data in results:
                all_data.extend(data)
            
            # Remove duplicates based on offer_id
            unique_data = []
            seen_ids = set()
            for item in all_data:
                if item['offer_id'] not in seen_ids:
                    seen_ids.add(item['offer_id'])
                    unique_data.append(item)
            
            # Track changes
            changes = track_changes(unique_data)
            
            # Send Telegram notifications
            bot = TelegramBot()
            if any(changes.values()):
                bot.send_tracking_updates(changes)
            
            # Print results
            print(f"\nTotal found {len(unique_data)} unique offers")
            if changes['new_offers']:
                print(f"🆕 {len(changes['new_offers'])} new offers found!")
            if changes['price_changes']:
                print(f"💰 {len(changes['price_changes'])} price changes detected!")
            if changes['removed_offers']:
                print(f"❌ {len(changes['removed_offers'])} offers removed")
            
            # Show detailed changes
            show_changes(changes)
            
            # Save current data
            with open('parsed_data.json', 'w', encoding='utf-8') as f:
                json.dump(unique_data, f, ensure_ascii=False, indent=2)
            
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(parse_cian())