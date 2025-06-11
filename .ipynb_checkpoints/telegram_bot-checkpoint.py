import requests
import os
from datetime import datetime


class TelegramBot:
    def __init__(self):
        self.bot_token = self._load_bot_token()
        self.chat_id = self._load_chat_id()
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def _load_bot_token(self):
        """Load bot token from file"""
        try:
            with open('bot_token.txt', 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            raise Exception("Bot token file not found. Please create bot_token.txt with your bot token.")

    def _load_chat_id(self):
        """Load chat ID from file"""
        try:
            with open('chat_id.txt', 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            raise Exception("Chat ID file not found. Please create chat_id.txt with your chat ID.")

    def _send_message(self, text, parse_mode='HTML'):
        """Send a message to Telegram"""
        url = f"{self.base_url}/sendMessage"
        data = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }
        
        try:
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error sending Telegram message: {e}")
            return False

    def _format_offer(self, offer):
        """Format offer data for Telegram message"""
        price_str = f"{offer['price']:,} ₽" if offer['price'] else "Цена не указана"
        metro_str = f"🚇 {offer['metro_station']}" if offer['metro_station'] else ""
        walking_time_str = f" ({offer['walking_time']})" if offer['walking_time'] else ""
        
        location = ""
        if offer.get('street'):
            location = f"📍 {offer['street']}"
            if offer.get('building_number'):
                location += f", {offer['building_number']}"
        
        rental_period = f"📅 {offer['rental_period']}" if offer.get('rental_period') else ""
        commission = f"💼 {offer['commission']}" if offer.get('commission') else ""
        deposit = f"💰 Залог: {offer['deposit']}" if offer.get('deposit') and offer['deposit'] != 'без залога' else ""
        
        details = []
        if metro_str:
            details.append(f"{metro_str}{walking_time_str}")
        if location:
            details.append(location)
        if rental_period:
            details.append(rental_period)
        if commission:
            details.append(commission)
        if deposit:
            details.append(deposit)
        
        details_str = "\n".join(details) if details else ""
        
        message = f"<b>{offer['title']}</b>\n"
        message += f"💵 <b>{price_str}</b>\n"
        if details_str:
            message += f"{details_str}\n"
        message += f"🔗 <a href=\"{offer['offer_url']}\">Посмотреть объявление</a>"
        
        return message

    def send_new_offer(self, offer):
        """Send notification about new offer"""
        header = "🆕 <b>НОВОЕ ПРЕДЛОЖЕНИЕ</b>\n\n"
        message = header + self._format_offer(offer)
        return self._send_message(message)

    def send_price_change(self, change):
        """Send notification about price change"""
        offer = change['offer']
        old_price = f"{change['old_price']:,} ₽"
        new_price = f"{change['new_price']:,} ₽"
        diff = change['price_diff']
        
        if diff > 0:
            direction = "📈"
            change_type = "ПОДОРОЖАНИЕ"
            diff_str = f"+{abs(diff):,} ₽"
        else:
            direction = "📉"
            change_type = "ПОДЕШЕВЛЕНИЕ"
            diff_str = f"-{abs(diff):,} ₽"
        
        header = f"{direction} <b>{change_type}</b>\n\n"
        price_info = f"💵 <b>{old_price} → {new_price}</b>\n"
        price_info += f"Изменение: <b>{diff_str}</b>\n\n"
        
        message = header + price_info + self._format_offer(offer)
        return self._send_message(message)

    def send_removed_offer(self, offer):
        """Send notification about removed offer"""
        header = "❌ <b>ПРЕДЛОЖЕНИЕ СНЯТО</b>\n\n"
        message = header + self._format_offer(offer)
        return self._send_message(message)

    def send_tracking_updates(self, changes):
        """Send all tracking updates"""
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        # Summary message
        summary_parts = []
        if changes['new_offers']:
            summary_parts.append(f"🆕 {len(changes['new_offers'])} новых")
        if changes['price_changes']:
            summary_parts.append(f"💰 {len(changes['price_changes'])} изменений цен")
        if changes['removed_offers']:
            summary_parts.append(f"❌ {len(changes['removed_offers'])} снятых")
        
        if summary_parts:
            summary = f"📊 <b>Обновление от {timestamp}</b>\n\n"
            summary += "Найдены изменения:\n" + "\n".join(f"• {part}" for part in summary_parts)
            self._send_message(summary)
        
        # Send new offers
        for offer in changes['new_offers']:
            self.send_new_offer(offer)
        
        # Send price changes
        for change in changes['price_changes']:
            self.send_price_change(change)
        
        # Send removed offers
        for offer in changes['removed_offers']:
            self.send_removed_offer(offer)

    def test_connection(self):
        """Test bot connection"""
        url = f"{self.base_url}/getMe"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            bot_info = response.json()
            if bot_info['ok']:
                print(f"✅ Bot connected successfully: @{bot_info['result']['username']}")
                return True
            else:
                print("❌ Bot connection failed")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Error testing bot connection: {e}")
            return False