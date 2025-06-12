import requests
import os
import yaml
from datetime import datetime


class TelegramBot:
    def __init__(self):
        self._load_config()
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def _load_config(self):
        """Load bot configuration from YAML file"""
        try:
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            
            self.bot_token = config['bot']['token']
            self.chat_ids = [str(id) for id in config['bot']['chat_ids']]
            
            if not self.bot_token or not self.chat_ids:
                raise Exception("Missing token or chat_ids in config.yaml")
        except FileNotFoundError:
            raise Exception("Configuration file not found. Please create config.yaml with bot token and chat IDs.")
        except KeyError as e:
            raise Exception(f"Invalid config.yaml structure: missing {e}")
        except Exception as e:
            raise Exception(f"Error reading config.yaml: {e}")

    def _send_message(self, text, parse_mode='HTML'):
        """Send a message to all Telegram chat IDs"""
        url = f"{self.base_url}/sendMessage"
        success = True
        
        for chat_id in self.chat_ids:
            data = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            
            try:
                response = requests.post(url, data=data, timeout=10)
                response.raise_for_status()
                print(f"✅ Message sent to chat {chat_id}")
            except requests.exceptions.RequestException as e:
                print(f"❌ Error sending to chat {chat_id}: {e}")
                success = False
        
        return success

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

    def _format_offer_without_price(self, offer):
        """Format offer data for Telegram message without price (for price change notifications)"""
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
            change_type = "ЦЕНА ВЫРОСЛА"
            diff_str = f"+{abs(diff):,} ₽"
        else:
            direction = "📉"
            change_type = "ЦЕНА СНИЗИЛАСЬ"
            diff_str = f"-{abs(diff):,} ₽"
        
        header = f"{direction} <b>{change_type}</b>\n\n"
        price_info = f"💵 <b>{old_price} → {new_price}</b> ({diff_str})\n\n"
        
        # Format offer without price (since we already show the price change above)
        offer_info = self._format_offer_without_price(offer)
        message = header + price_info + offer_info
        return self._send_message(message)

    def send_removed_offer(self, offer):
        """Send notification about removed offer"""
        header = "❌ <b>ПРЕДЛОЖЕНИЕ СНЯТО</b>\n\n"
        message = header + self._format_offer(offer)
        return self._send_message(message)

    def send_tracking_updates(self, changes):
        """Send all tracking updates"""
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
                print(f"   Will send to {len(self.chat_ids)} chat(s): {', '.join(self.chat_ids)}")
                return True
            else:
                print("❌ Bot connection failed")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Error testing bot connection: {e}")
            return False