# Tychra

[![Release builder](https://github.com/VikStoykov/Tychra/actions/workflows/release.yml/badge.svg)](https://github.com/VikStoykov/Tychra/actions/workflows/release.yml)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Discord](https://img.shields.io/badge/discord.py-2.6.4-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

<div align="center">
  <img src="./images/logo_name.png" alt="Tychra Logo" width="300" height="300">
</div>

**A Discord bot that tracks market sentiment indicators and displays them in real-time**

---

## Features

- 📊 **Live Market Data** - Fetches CNN Fear & Greed Index automatically
- 🤖 **Dynamic Updates** - Changes bot nickname and status based on market sentiment
- ⏰ **Scheduled Updates** - Configurable automatic updates with timezone support
- 🎨 **Customizable Templates** - Create your own display format per server
- 🐳 **Docker Ready** - Easy deployment with Docker and docker-compose
- 🆓 **Free & Open Source** - No API keys required (uses public data)

## Quick Start

### Prerequisites

- Python 3.9+
- Discord Bot Token ([Get one here](https://discord.com/developers/applications))
- Docker (optional, for containerized deployment)

### Installation

#### Option 1: Local Installation

```bash
# Clone the repository
git clone https://github.com/VikStoykov/Tychra.git
cd Tychra

# Create virtual environment
python3 -m venv bot-env
source bot-env/bin/activate  # On Windows: bot-env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your DISCORD_TOKEN

# Run the bot
python3 main.py
```

#### Option 2: Docker

```bash
# Pull the image
docker pull vikstoykov/tychra:latest

# Run with environment file
docker run -d \
  --name tychra-bot \
  --env-file .env \
  --restart unless-stopped \
  vikstoykov/tychra:latest
```

#### Option 3: Docker Compose

```bash
# Edit .env file with your settings
docker-compose up -d
```

## Configuration

Create a `.env` file with the following variables:

```env
# Required: Your Discord bot token
DISCORD_TOKEN=your_discord_bot_token_here

# Optional: Timezone for scheduled updates (default: UTC)
TIMEZONE=UTC

# Optional: Scheduled update times (comma-separated, 24-hour format)
UPDATE_TIMES=09:00,18:00
```

### Timezone Examples

```env
# UTC (default)
TIMEZONE=UTC

# Eastern Time
TIMEZONE=America/New_York

# European time zones
TIMEZONE=Europe/London
TIMEZONE=Europe/Sofia

# Asian time zones
TIMEZONE=Asia/Tokyo
```

## Discord Commands

All commands require "Manage Server" permission:

- `/setnickname <template>` - Set the bot's nickname template
- `/setstatus <template>` - Set the bot's status template
- `/showtemplates` - View current templates and available placeholders
- `/forceupdate` - Trigger an immediate update
- `/about` - Show bot information

### Template Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{m.index}` | Market index (0-100) | `42` |
| `{m.emotion}` | Market emotion | `Fear` |
| `{m.emoji}` | Market emoji | `😨` |
| `{m.trend}` | Market trend | `↘️ falling` |

### Template Examples

```bash
# Simple index display
/setnickname F/G: {m.index}

# With emoji
/setnickname {m.emoji} {m.index}

# Full status
/setstatus {m.emotion} {m.emoji} - {m.trend}
```

## Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and name it (e.g., "Tychra")
3. Go to "Bot" section and click "Add Bot"
4. Copy your bot token
5. Under "Bot Permissions", enable:
   - Change Nickname
   - Send Messages
   - Use Slash Commands
6. Go to "OAuth2" → "URL Generator"
7. Select scopes: `bot` and `applications.commands`
8. Select permissions: `Change Nickname`, `Send Messages`
9. Use the generated URL to invite the bot to your server

## Data Sources

- **Stock Market**: [CNN Fear & Greed Index](https://money.cnn.com/data/fear-and-greed/)

## License

MIT License - see [LICENSE](LICENSE) for details.
