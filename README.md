# Discord Moderation Bot

A complete, production-ready Discord moderation bot built with discord.py featuring comprehensive moderation tools.

## Features

- **User Management**
  - Kick members
  - Ban members
  - Mute/Unmute members with custom durations
  
- **Warning System**
  - Warn members
  - Automatic ban after reaching max warnings
  - View warning history
  - Clear warnings
  
- **Case Tracking**
  - Track all moderation actions
  - View moderation history per user
  - View all guild cases
  
- **Permission-Based**
  - Only moderators can use moderation commands
  - Hierarchy checks (can't moderate equal or higher roles)
  
- **Database Persistence**
  - SQLite database for warnings and cases
  - Persistent moderation history

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Setup Steps

1. **Clone/Create Project**
   ```bash
   cd botdc
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Bot**
   - Copy `.env.example` to `.env`
   - Add your Discord bot token to `.env`
   ```
   DISCORD_TOKEN=your_bot_token_here
   DISCORD_PREFIX=!
   ```

4. **Run the Bot**
   ```bash
   python main.py
   ```

## Commands

### Moderation Commands
- `!kick @user [reason]` - Kick a user from the server
- `!ban @user [reason]` - Ban a user from the server
- `!warn @user [reason]` - Warn a user
- `!mute @user [duration] [reason]` - Mute a user (e.g., 10m, 1h, 2d)
- `!unmute @user [reason]` - Unmute a user
- `!clearwarnings @user` - Clear all warnings for a user

### Information Commands
- `!warnings [@user]` - Check warnings (yours or another user's)
- `!cases [@user]` - View moderation cases
- `!help` - Show help message
- `!ping` - Check bot latency

## Configuration ⚙️

Edit `config.py` to customize:
- `MAX_WARNINGS` - Number of warnings before automatic ban (default: 5)
- `COLOR_*` - Embed colors for different message types
- `DB_PATH` - Database file location

## Project Structure

```
botdc/
├── main.py              # Bot entry point
├── config.py            # Configuration settings
├── requirements.txt     # Python dependencies
├── .env.example         # Example environment variables
├── cogs/
│   ├── moderation.py    # Moderation commands
│   └── info.py          # Information commands
├── utils/
│   ├── permissions.py   # Permission checking
│   └── database.py      # Database operations
└── README.md            # This file
```

## Creating a Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Go to "Bot" tab and click "Add Bot"
4. Copy the token and add it to `.env`
5. Under "OAuth2" > "URL Generator", select:
   - Scopes: `bot`
   - Permissions: `Moderate Members`, `Kick Members`, `Ban Members`, `Send Messages`, `Manage Messages`, `Read Message History`
6. Use the generated URL to invite the bot to your server

## Bot Permissions Required

For the bot to function properly, ensure it has these permissions:
- Moderate Members (for mute/unmute)
- Kick Members
- Ban Members
- Send Messages
- Embed Links
- Read Message History

## Support & Troubleshooting

### Bot won't start
- Check if `DISCORD_TOKEN` is set in `.env`
- Ensure the token is valid and not expired
- Check Python version (3.8+)

### Command not working
- Verify bot has required permissions
- Check bot role hierarchy
- Ensure moderator has required permissions

### Database errors
- Delete `moderation.db` and restart bot to reinitialize
- Ensure write permissions in the directory

## License

This project is open source and available under the MIT License.

---

-kyurem, with the help of AI
