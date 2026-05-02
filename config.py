"""
Configuration settings for the Discord bot
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Bot settings
TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = os.getenv('DISCORD_PREFIX', '!')

# Database
DB_PATH = 'moderation.db'

# Colors for embeds
COLOR_SUCCESS = 0x2ECC71
COLOR_ERROR = 0xE74C3C
COLOR_INFO = 0x3498DB
COLOR_WARNING = 0xF1C40F
COLOR_HIGHLIGHT = 0x9B59B6
COLOR_DARK = 0x2C3E50

# Maximum warnings before automatic ban
MAX_WARNINGS = 20

# Default command permission levels
DEFAULT_COMMAND_LEVELS = {
    'help': 1,
    'ping': 1,
    'warnings': 1,
    'snipe': 1,
    'cases': 2,
    'kick': 2,
    'ban': 2,
    'warn': 2,
    'mute': 2,
    'unmute': 2,
    'clearwarnings': 2,
    'ticket': 2,
    'ticket create': 2,
    'ticket close': 2,
    'ticket setup': 3,
    'freeze': 2,
    'unfreeze': 2,
    'embed': 3,
    'blacklist': 3,
    'blacklist add': 3,
    'blacklist remove': 4,
    'blacklist list': 3,
    'perm': 3,
    'perm set': 3,
    'perm check': 2,
    'permconfig': 4,
    'permconfig set': 4,
    'permconfig show': 3,
    'massrole': 4,
    'massban': 4,
    'massmute': 4,
    'moveall': 4,
    'mutegroup': 4,
    'wordban': 3,
    'wordban add': 3,
    'wordban remove': 4,
    'wordban list': 3,
    'log': 3,
    'log set': 4,
    'log show': 3,
    'log off': 4,
    'pic': 1,
}

LEVEL_NAMES = {
    1: 'Membre',
    2: 'Modérateur',
    3: 'Manager',
    4: 'Administrateur',
}
