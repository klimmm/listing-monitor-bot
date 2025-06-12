# Telegram Bot for Real Estate Monitoring

This bot monitors real estate listings and sends Telegram notifications for:
- New offers
- Price changes
- Removed offers

## Configuration

The bot uses YAML configuration files and environment variables:

### Environment Variables (Recommended)

Set these environment variables for secure configuration:

```bash
# Required
export BOT_TOKEN="your_telegram_bot_token"
export BASE_URL="your_base_url_here"
export GITHUB_TOKEN="your_github_token"  # For workflow automation
```

**For permanent local setup:**
```bash
# Add to ~/.zshrc or ~/.bashrc
echo 'export BOT_TOKEN="your_bot_token"' >> ~/.zshrc
echo 'export BASE_URL="your_base_url"' >> ~/.zshrc
source ~/.zshrc
```

**Alternative: .env file (local development only)**
```bash
# Create .env file in project directory
BOT_TOKEN=your_telegram_bot_token
BASE_URL=your_base_url_here
GITHUB_TOKEN=your_github_token
```

### 1. Telegram Configuration (`config_telegram.yaml`)
```yaml
token: YOUR_BOT_TOKEN_HERE  # Will be overridden by BOT_TOKEN env var
chat_ids:
  - 252024578
  # Add more chat IDs below
max_retries: 3
retry_delay: 1  # Initial delay in seconds
max_delay: 30   # Maximum delay between retries
```

### 2. Search Configuration (`config_search.yaml`)
```yaml
# Maximum price in rubles
maxprice: 85000

# Districts (by ID)
district:
  - 21  # Хамовники
  - 13  # Арбат
  - 22  # Якиманка

# Room types (leave empty for all)
rooms: []

# Streets (by ID)
street: 
  - 685   # Бережковская набережная
  - 2306  # Украинский бульвар
  - 2616  # наб. Тараса Шевченко
  - 1246  # Косыгина
  - 1150  # Капранова пер.
  - 1598  # Николаева ул.
```

### 3. Browser Configuration (`config_browser.yaml`)
```yaml
user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
args:
  - '--disable-blink-features=AutomationControlled'
headless: true
wait_until: 'domcontentloaded'
timeouts:
  wait_until: 15000
  wait_for_function: 10000
```

### 4. Scripts Configuration (`config_scripts.yaml`)
Contains JavaScript code for web scraping (automatically configured).

## How to get Telegram credentials:

**Bot Token:**
1. Message @BotFather on Telegram
2. Create a new bot with `/newbot`
3. Copy the provided token

**Chat ID:**
1. Add your bot to the chat/group or start a conversation
2. Send a message to the bot
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Find your chat ID in the response

## Running the Bot

### Local Development
1. Set environment variables (see Configuration section above)
2. Configure YAML files with your settings
3. Install dependencies: `pip install playwright requests pyyaml python-dotenv`
4. Install browsers: `playwright install chromium`
5. Run: `python parser.py`

### GitHub Actions (Automated)
The repository includes GitHub Actions workflow for automated execution:
- Runs every 5 minutes
- Uses repository secrets: `BOT_TOKEN`, `BASE_URL`
- No manual configuration needed once secrets are set

### Manual Workflow Trigger
Use environment variable for security:
```bash
export GITHUB_TOKEN="your_github_token"
./trigger_workflow.sh
```

## Files

- `parser.py` - Main scraper with automatic pagination and change detection
- `telegram_bot.py` - Telegram notification handler with retry logic
- `helpers.py` - Utility functions for URL construction, change tracking, and message formatting
- `config_*.yaml` - Configuration files for different components
- `current_data.json` - Current offer data (auto-updated)
- `trigger_workflow.sh` - Script for automated execution (local only, not tracked)
- `.env` - Environment variables file (local only, not tracked)
- `.github/workflows/telegram_bot.yml` - GitHub Actions workflow configuration

## Security Notes

- Environment variables are prioritized over config files
- Sensitive data (tokens, URLs) should use environment variables
- Local files like `.env`, `bot_token.txt`, `base_url.txt` are gitignored
- GitHub Actions uses repository secrets for secure configuration