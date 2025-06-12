#!/bin/bash

# Read token from file
TOKEN=$(cat ~/Desktop/сian/app/telegram/github_token.txt)

curl -X POST \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/klimmm/cian-telegram-bot/actions/workflows/telegram_bot.yml/dispatches \
  -d '{"ref":"main"}'

echo "Workflow triggered!"