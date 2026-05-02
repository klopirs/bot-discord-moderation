"""
Database utilities for storing moderation data
"""
import aiosqlite
from config import DB_PATH

async def init_db():
    """Initialize the database"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                reason TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        await db.execute('''
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                reason TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        await db.execute('''
            CREATE TABLE IF NOT EXISTS mutes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                reason TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        await db.execute('''
            CREATE TABLE IF NOT EXISTS blacklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                reason TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, user_id)
            )
        ''')

        await db.execute('''
            CREATE TABLE IF NOT EXISTS permission_levels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                level INTEGER NOT NULL,
                UNIQUE(guild_id, user_id)
            )
        ''')

        await db.execute('''
            CREATE TABLE IF NOT EXISTS command_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                command_name TEXT NOT NULL,
                level INTEGER NOT NULL,
                UNIQUE(guild_id, command_name)
            )
        ''')

        await db.execute('''
            CREATE TABLE IF NOT EXISTS snipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT,
                attachments TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        await db.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                owner_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        await db.execute('''
            CREATE TABLE IF NOT EXISTS banned_words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                word TEXT NOT NULL,
                moderator_id INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, word)
            )
        ''')

        await db.execute('''
            CREATE TABLE IF NOT EXISTS guild_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                setting_key TEXT NOT NULL,
                setting_value TEXT NOT NULL,
                UNIQUE(guild_id, setting_key)
            )
        ''')

        await db.execute('''
            CREATE TABLE IF NOT EXISTS action_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                target_id INTEGER,
                moderator_id INTEGER,
                details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        await db.commit()

# Warning helpers
async def add_warning(user_id: int, guild_id: int, moderator_id: int, reason: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT INTO warnings (user_id, guild_id, moderator_id, reason) VALUES (?, ?, ?, ?)',
            (user_id, guild_id, moderator_id, reason)
        )
        await db.commit()

async def get_warnings(user_id: int, guild_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            'SELECT COUNT(*) FROM warnings WHERE user_id = ? AND guild_id = ?',
            (user_id, guild_id)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def get_user_warnings(user_id: int, guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            'SELECT * FROM warnings WHERE user_id = ? AND guild_id = ? ORDER BY timestamp DESC',
            (user_id, guild_id)
        ) as cursor:
            return await cursor.fetchall()

async def clear_warnings(user_id: int, guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'DELETE FROM warnings WHERE user_id = ? AND guild_id = ?',
            (user_id, guild_id)
        )
        await db.commit()

# Case helpers
async def add_case(guild_id: int, action: str, user_id: int, moderator_id: int, reason: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT INTO cases (guild_id, action, user_id, moderator_id, reason) VALUES (?, ?, ?, ?, ?)',
            (guild_id, action, user_id, moderator_id, reason)
        )
        await db.commit()

async def get_cases(guild_id: int, user_id: int = None):
    async with aiosqlite.connect(DB_PATH) as db:
        if user_id:
            query = 'SELECT * FROM cases WHERE guild_id = ? AND user_id = ? ORDER BY timestamp DESC'
            async with db.execute(query, (guild_id, user_id)) as cursor:
                return await cursor.fetchall()
        else:
            query = 'SELECT * FROM cases WHERE guild_id = ? ORDER BY timestamp DESC'
            async with db.execute(query, (guild_id,)) as cursor:
                return await cursor.fetchall()

# Blacklist helpers
async def add_blacklist(user_id: int, guild_id: int, moderator_id: int, reason: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT OR REPLACE INTO blacklist (user_id, guild_id, moderator_id, reason) VALUES (?, ?, ?, ?)',
            (user_id, guild_id, moderator_id, reason)
        )
        await db.commit()

async def remove_blacklist(user_id: int, guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'DELETE FROM blacklist WHERE user_id = ? AND guild_id = ?',
            (user_id, guild_id)
        )
        await db.commit()

async def get_blacklist(user_id: int, guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            'SELECT * FROM blacklist WHERE user_id = ? AND guild_id = ?',
            (user_id, guild_id)
        ) as cursor:
            return await cursor.fetchone()

async def list_blacklist(guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            'SELECT user_id, reason, moderator_id, timestamp FROM blacklist WHERE guild_id = ?',
            (guild_id,)
        ) as cursor:
            return await cursor.fetchall()

# Permission helpers
async def set_user_permission(user_id: int, guild_id: int, level: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT OR REPLACE INTO permission_levels (user_id, guild_id, level) VALUES (?, ?, ?)',
            (user_id, guild_id, level)
        )
        await db.commit()

async def get_user_permission_level(user_id: int, guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            'SELECT level FROM permission_levels WHERE user_id = ? AND guild_id = ?',
            (user_id, guild_id)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def remove_user_permission(user_id: int, guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'DELETE FROM permission_levels WHERE user_id = ? AND guild_id = ?',
            (user_id, guild_id)
        )
        await db.commit()

# Command permission helpers
async def set_command_permission(guild_id: int, command_name: str, level: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT OR REPLACE INTO command_permissions (guild_id, command_name, level) VALUES (?, ?, ?)',
            (guild_id, command_name, level)
        )
        await db.commit()

async def get_command_permission_level(guild_id: int, command_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            'SELECT level FROM command_permissions WHERE guild_id = ? AND command_name = ?',
            (guild_id, command_name)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

# Snipe helpers
async def add_snipe(guild_id: int, channel_id: int, user_id: int, content: str, attachments: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT INTO snipes (guild_id, channel_id, user_id, content, attachments) VALUES (?, ?, ?, ?, ?)',
            (guild_id, channel_id, user_id, content, attachments)
        )
        await db.commit()

async def get_snipe(guild_id: int, channel_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            'SELECT user_id, content, attachments, timestamp FROM snipes WHERE guild_id = ? AND channel_id = ? ORDER BY timestamp DESC LIMIT 1',
            (guild_id, channel_id)
        ) as cursor:
            return await cursor.fetchone()

# Ticket helpers
async def create_ticket(guild_id: int, channel_id: int, owner_id: int, status: str = 'open'):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT INTO tickets (guild_id, channel_id, owner_id, status) VALUES (?, ?, ?, ?)',
            (guild_id, channel_id, owner_id, status)
        )
        await db.commit()

async def close_ticket(channel_id: int, guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'UPDATE tickets SET status = ? WHERE channel_id = ? AND guild_id = ?',
            ('closed', channel_id, guild_id)
        )
        await db.commit()

async def get_ticket(channel_id: int, guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            'SELECT * FROM tickets WHERE channel_id = ? AND guild_id = ?',
            (channel_id, guild_id)
        ) as cursor:
            return await cursor.fetchone()
# Banned word helpers
async def add_banned_word(guild_id: int, word: str, moderator_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT OR REPLACE INTO banned_words (guild_id, word, moderator_id) VALUES (?, ?, ?)',
            (guild_id, word.lower(), moderator_id)
        )
        await db.commit()

async def remove_banned_word(guild_id: int, word: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'DELETE FROM banned_words WHERE guild_id = ? AND word = ?',
            (guild_id, word.lower())
        )
        await db.commit()

async def list_banned_words(guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            'SELECT word, moderator_id, timestamp FROM banned_words WHERE guild_id = ? ORDER BY timestamp DESC',
            (guild_id,)
        ) as cursor:
            return await cursor.fetchall()

# Guild settings helpers
async def set_guild_setting(guild_id: int, key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT OR REPLACE INTO guild_settings (guild_id, setting_key, setting_value) VALUES (?, ?, ?)',
            (guild_id, key, value)
        )
        await db.commit()

async def get_guild_setting(guild_id: int, key: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            'SELECT setting_value FROM guild_settings WHERE guild_id = ? AND setting_key = ?',
            (guild_id, key)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def remove_guild_setting(guild_id: int, key: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'DELETE FROM guild_settings WHERE guild_id = ? AND setting_key = ?',
            (guild_id, key)
        )
        await db.commit()

# Action log helpers
async def add_action_log(guild_id: int, action: str, target_id: int = None, moderator_id: int = None, details: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT INTO action_logs (guild_id, action, target_id, moderator_id, details) VALUES (?, ?, ?, ?, ?)',
            (guild_id, action, target_id, moderator_id, details)
        )
        await db.commit()