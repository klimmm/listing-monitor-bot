import asyncio
import json
from playwright.async_api import async_playwright


async def parse_cian():
    # Read URLs from file
    with open('url.txt', 'r') as f:
        urls = [line.strip() for line in f.readlines() if line.strip() and line.strip().startswith('http')]
    
    # Read scripts from JS file
    with open('scripts.js', 'r') as f:
        js_content = f.read()
    
    # Extract the functions from the JS file
    # The primary_script function
    primary_script_start = js_content.find('const primary_script = () => {')
    primary_script_end = js_content.find('};', primary_script_start) + 2
    primary_script = js_content[primary_script_start:primary_script_end].replace('const primary_script = ', '').strip()
    
    # The wait_for_function
    wait_start = js_content.find('const wait_for_function = () => {')
    wait_end = js_content.find('};', wait_start) + 2
    wait_for_function = js_content[wait_start:wait_end].replace('const wait_for_function = ', '').strip()
    
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
                    
                    # Additional wait to ensure all content is loaded
                    await page.wait_for_timeout(3000)
                    
                    # Scroll to load any lazy-loaded content
                    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await page.wait_for_timeout(2000)
                    
                    # Try scrolling multiple times to trigger lazy loading
                    for j in range(3):
                        await page.evaluate('window.scrollBy(0, 1000)')
                        await page.wait_for_timeout(1000)
                    
                    # Check how many cards are present
                    card_count = await page.evaluate('document.querySelectorAll(\'[data-name="Offers"] [data-name="CardComponent"]\').length')
                    print(f"Found {card_count} CardComponent elements in Offers container")
                    
                    # Execute the primary script to extract data
                    data = await page.evaluate(primary_script)
                    
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