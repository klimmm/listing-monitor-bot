import asyncio
import json
import yaml
from datetime import datetime, timedelta
import re
from playwright.async_api import async_playwright
from parse_date import parse_russian_date


async def parse_cian():
    # Read URLs from file
    with open('url.txt', 'r') as f:
        urls = [line.strip() for line in f.readlines() if line.strip() and line.strip().startswith('http')]
    
    # Read scripts from YAML file
    with open('scripts.yaml', 'r') as f:
        scripts = yaml.safe_load(f)
    
    primary_script = scripts['primary_script']
    wait_for_function = scripts['wait_for_function']
    
    all_data = []
    
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
            for i, url in enumerate(urls):
                print(f"\nParsing URL {i+1}/{len(urls)}: {url[:80]}...")
                
                page = await context.new_page()
                
                try:
                    # Navigate to URL
                    await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                    
                    # Wait for content to load using the wait function
                    await page.wait_for_function(wait_for_function, timeout=30000)
                    
                    # Execute the primary script to extract data
                    data = await page.evaluate(primary_script)
                    
                    # Process dates in Python
                    for item in data:
                        if 'time_label' in item and item['time_label']:
                            item['time_label'] = parse_russian_date(item['time_label'])
                    
                    print(f"Found {len(data)} offers on this page")
                    all_data.extend(data)
                    
                finally:
                    await page.close()
            
            # Remove duplicates based on offer_id
            unique_data = []
            seen_ids = set()
            for item in all_data:
                if item['offer_id'] not in seen_ids:
                    seen_ids.add(item['offer_id'])
                    unique_data.append(item)
            
            # Print results
            print(f"\nTotal found {len(unique_data)} unique offers:")
            print(json.dumps(unique_data, ensure_ascii=False, indent=2))
            
            # Save to file
            with open('parsed_data.json', 'w', encoding='utf-8') as f:
                json.dump(unique_data, f, ensure_ascii=False, indent=2)
            
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(parse_cian())