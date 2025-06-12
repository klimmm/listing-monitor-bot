# Telegram Bot for Cian Real Estate Monitoring

This bot monitors Cian real estate listings and sends Telegram notifications for:
- New offers
- Price changes
- Removed offers

## GitHub Actions Setup

### 1. Repository Secrets

Add these secrets to your GitHub repository (`Settings` > `Secrets and variables` > `Actions`):

- `BOT_TOKEN`: Your Telegram bot token from @BotFather
- `CHAT_ID`: Your Telegram chat ID (can be personal chat or group)

### 2. How to get credentials:

**Bot Token:**
1. Message @BotFather on Telegram
2. Create a new bot with `/newbot`
3. Copy the provided token

**Chat ID:**
1. Add your bot to the chat/group or start a conversation
2. Send a message to the bot
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Find your chat ID in the response

### 3. Workflow Schedule

The bot runs automatically every 5 minutes. You can also trigger it manually from the Actions tab.

## Local Development

1. Create `bot_config.txt` with:
   ```
   BOT_TOKEN=your_bot_token_here
   CHAT_ID=chat_id_1,chat_id_2,chat_id_3
   ```
   Note: You can use a single chat ID or multiple IDs separated by commas
2. Run: `python parse_cian.py`

## Files

- `parse_cian.py` - Main scraper with change detection
- `telegram_bot.py` - Telegram notification handler
- `scripts.yaml` - Web scraping scripts
- `url.txt` - URLs to monitor
- `parsed_data.json` - Current offer data (auto-updated)