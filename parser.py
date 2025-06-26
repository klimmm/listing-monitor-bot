import asyncio
import json
import yaml
import os
from playwright.async_api import async_playwright
from telegram_bot import TelegramBot
from helpers import track_changes, construct_search_url, normalize_offer_data

# Load .env file if it exists
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # dotenv not installed, skip
    pass


async def parse_single_url(context, url, browser_config, scripts):
    """Parse a single URL and return offers"""
    print(f"\nParsing: {url[:200]}...")

    page = await context.new_page()

    try:
        # Navigate to URL
        await page.goto(
            url,
            wait_until=browser_config["wait_until"],
            timeout=browser_config["timeouts"]["wait_until"],
        )

        # Wait for content to load using the wait function
        await page.wait_for_function(
            scripts["wait_for_function"],
            timeout=browser_config["timeouts"]["wait_for_function"],
        )

        # Execute the primary script to extract data
        data = await page.evaluate(scripts["primary_script"])

        print(f"Found {len(data)} offers")
        return data

    except Exception as e:
        print(f"Error parsing URL: {e}")
        raise e  # Re-raise the exception instead of returning empty array

    finally:
        await page.close()


async def parse_with_auto_pagination(base_url, browser_config, scripts, max_pages=20):
    """Parse URL with automatic pagination detection"""

    # Read scripts from YAML file
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(
            headless=browser_config["headless"], args=browser_config["args"]
        )
        context = await browser.new_context(user_agent=browser_config["user_agent"])

        try:
            unique_offers = {}

            print(f"\n{'='*60}")

            for page_num in range(1, max_pages + 1):
                # Generate URL for this page
                page_url = f"{base_url}&p={page_num}"

                # Parse this page
                page_offers = await parse_single_url(
                    context, page_url, browser_config, scripts
                )

                # Check for new offers
                new_offers_count = 0
                for offer in page_offers:
                    offer_id = offer.get("offer_id")
                    if offer_id and offer_id not in unique_offers:
                        unique_offers[offer_id] = offer
                        new_offers_count += 1

                print(f"Page {page_num}: {new_offers_count} unique offers")

                # If no new offers found, increment counter
                if new_offers_count == 0:
                    break

            unique_offers_list = list(unique_offers.values())

            print(f"\n🎯 TOTAL UNIQUE OFFERS: {len(unique_offers_list)}")

            return unique_offers_list

        finally:
            await browser.close()


async def parse_listings_auto(data_file="data/current_data.json"):
    """Main function with automatic pagination"""

    with open("configs/config_search.yaml", "r") as f:
        search_config = yaml.safe_load(f)
    with open("configs/config_browser.yaml", "r") as f:
        browser_config = yaml.safe_load(f)
    with open("configs/config_scripts.yaml", "r") as f:
        scripts = yaml.safe_load(f)
    with open("configs/config_telegram.yaml", "r") as f:
        telegram_config = yaml.safe_load(f)
    bot_token = os.getenv("BOT_TOKEN")
    if bot_token:
        telegram_config["token"] = bot_token
        print("🔑 Using bot token from BOT_TOKEN environment variable")

    print("\nSearch parameters:")
    for key, value in search_config.items():
        print(f"  {key}: {value}")
    
    try:
        # Generate base URL
        base_url = construct_search_url(search_config)
        current_data = await parse_with_auto_pagination(base_url, browser_config, scripts)

        # Normalize offer data (parse dates, etc.)
        current_data = normalize_offer_data(current_data)

        # Track changes
        with open(data_file, "r", encoding="utf-8") as f:
            previous_data = json.load(f)
        changes = track_changes(current_data, previous_data)

        # Send Telegram notifications (disabled for testing)
        # bot = TelegramBot(telegram_config)
        # if changes:
        #     bot.send_tracking_updates(changes)
        print(f"🔕 Telegram notifications disabled for testing")

        # Create workflow trigger flags
        os.makedirs("data", exist_ok=True)
        
        # Categorize changes
        has_new = any("current_offer" in change and "previous_offer" not in change for change in changes)
        has_removed = any("previous_offer" in change and "current_offer" not in change for change in changes)
        has_price_changes = any("current_offer" in change and "previous_offer" in change for change in changes)
        
        if has_removed:
            with open("data/workflow_trigger", "w") as f:
                f.write("mode=update\nsearch=narrow")
        elif has_new or has_price_changes:
            with open("data/workflow_trigger", "w") as f:
                f.write("mode=new\nsearch=narrow")

        # Save current data
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(current_data, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"❌ PARSING FAILED: {e}")
        print("🛡️  Preserving existing data - no changes made to current_data.json")
        # Exit with error code so GitHub Actions knows it failed
        exit(1)


if __name__ == "__main__":
    asyncio.run(parse_listings_auto())
