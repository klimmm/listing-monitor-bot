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

The bot runs automatically every 30 minutes. You can also trigger it manually from the Actions tab.

## Local Development

1. Create `bot_token.txt` with your bot token
2. Create `chat_id.txt` with your chat ID  
3. Run: `python parse_cian.py`

## Files

- `parse_cian.py` - Main scraper with change detection
- `telegram_bot.py` - Telegram notification handler
- `scripts.yaml` - Web scraping scripts
- `url.txt` - URLs to monitor
- `parsed_data.json` - Current offer data (auto-updated)