import requests
import time
from helpers import format_change


class TelegramBot:
    def __init__(self, config):
        self.bot_token = config["token"]
        self.chat_ids = [str(id) for id in config["chat_ids"]]
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.max_retries = config.get("max_retries", 3)
        self.retry_delay = config.get("retry_delay", 1)
        self.max_delay = config.get("max_delay", 30)

    def send_message_with_retry(self, chat_id, text, parse_mode="HTML"):
        """Send a message to a single chat with retry logic"""
        url = f"{self.base_url}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": False,
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.post(url, data=data, timeout=10)
                response.raise_for_status()
                print(f"✅ Message sent to chat {chat_id}")
                return True

            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    # Calculate delay with exponential backoff
                    delay = min(self.retry_delay * (2**attempt), self.max_delay)
                    print(f"⚠️  Attempt {attempt + 1} failed for chat {chat_id}: {e}")
                    print(f"⏳ Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    print(f"❌ All attempts failed for chat {chat_id}: {e}")
                    return False

        return False

    def send_message(self, text, parse_mode="HTML"):
        """Send a message to all Telegram chat IDs with retry logic"""
        success_count = 0
        failed_chats = []

        for i, chat_id in enumerate(self.chat_ids):
            # Add a small delay between messages to avoid rate limiting
            if i > 0:
                time.sleep(0.5)

            if self.send_message_with_retry(chat_id, text, parse_mode):
                success_count += 1
            else:
                failed_chats.append(chat_id)

        # Summary
        if failed_chats:
            print(
                f"\n📊 Summary: {success_count}/{len(self.chat_ids)} messages sent successfully"
            )
            print(f"❌ Failed chats: {', '.join(failed_chats)}")
        else:
            print(f"\n✅ All {success_count} messages sent successfully!")

    def send_tracking_updates(self, changes):
        """Send all tracking updates with rate limiting"""

        # Process all changes with the unified formatter
        for index, change in enumerate(changes, 1):
            print(f"\n📨 Sending message {index}/{len(changes)}...")
            message = format_change(change)
            self.send_message(message)

            # Add delay between messages to avoid rate limiting
            if index < len(changes):
                time.sleep(1)