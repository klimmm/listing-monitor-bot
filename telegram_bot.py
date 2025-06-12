import requests
import time
import json
import os
from datetime import datetime
from helpers import format_change


class TelegramBot:
    def __init__(self, config):
        self.bot_token = config["token"]
        self.chat_ids = [str(id) for id in config["chat_ids"]]
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.max_retries = config.get("max_retries", 3)
        self.retry_delay = config.get("retry_delay", 1)
        self.max_delay = config.get("max_delay", 30)
        self.message_log_file = config.get("message_log_file", "data/telegram_messages.json")

    def _log_message(self, chat_id, text, success, error_message=None):
        """Log sent message to JSON file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.message_log_file), exist_ok=True)
            
            # Load existing messages
            messages = []
            if os.path.exists(self.message_log_file):
                try:
                    with open(self.message_log_file, 'r', encoding='utf-8') as f:
                        messages = json.load(f)
                except json.JSONDecodeError:
                    messages = []
            
            # Create message entry
            message_entry = {
                "timestamp": datetime.now().isoformat(),
                "chat_id": chat_id,
                "text": text,
                "success": success,
                "error_message": error_message
            }
            
            messages.append(message_entry)
            
            # Save updated messages
            with open(self.message_log_file, 'w', encoding='utf-8') as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"⚠️  Failed to log message: {e}")

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
                self._log_message(chat_id, text, success=True)
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
                    self._log_message(chat_id, text, success=False, error_message=str(e))
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