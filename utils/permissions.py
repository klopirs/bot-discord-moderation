"""
Permission checking utilities
"""
import discord
from discord.ext import commands
from utils.database import get_user_permission_level, get_command_permission_level, get_blacklist
import config

async def get_permission_level(member: discord.Member) -> int:
    """Get the effective permission level for a member"""
    if member.guild is None:
        return 1

    # Server owner always has level 4
    if member == member.guild.owner:
        return 4

    # Users with administrator permission have level 4
    if member.guild_permissions.administrator:
        return 4

    # Users with manage_guild permission have level 4
    if member.guild_permissions.manage_guild:
        return 4

    custom_level = await get_user_permission_level(member.id, member.guild.id)
    if custom_level:
        return max(1, min(4, custom_level))

    if member.guild_permissions.moderate_members or member.guild_permissions.kick_members or member.guild_permissions.ban_members or member.guild_permissions.manage_messages:
        return 2

    return 1

async def is_blacklisted(member: discord.Member) -> bool:
    """Check if a member is blacklisted in the guild"""
    if member.guild is None:
        return False
    row = await get_blacklist(member.id, member.guild.id)
    return bool(row)

async def get_required_command_level(ctx) -> int:
    """Get the required permission level for a command"""
    if ctx.guild is None:
        return 4

    qualified = ctx.command.qualified_name if ctx.command else ''
    level = await get_command_permission_level(ctx.guild.id, qualified)
    if level:
        return max(1, min(4, level))

    if ctx.command:
        root = ctx.command.root_parent.name if ctx.command.root_parent else ctx.command.name
        return config.DEFAULT_COMMAND_LEVELS.get(root, config.DEFAULT_COMMAND_LEVELS.get(ctx.command.name, 1))

    return 1

async def has_command_permission(ctx) -> bool:
    """Check whether the user can use the invoked command"""
    if ctx.guild is None:
        return False

    if await is_blacklisted(ctx.author):
        return False

    user_level = await get_permission_level(ctx.author)
    required_level = await get_required_command_level(ctx)
    return user_level >= required_level

def permission_level(level: int):
    """Return a command check requiring a minimum permission level"""
    async def predicate(ctx):
        if await is_blacklisted(ctx.author):
            raise commands.CheckFailure("blacklisted")
        if await get_permission_level(ctx.author) < level:
            raise commands.CheckFailure("permission level too low")
        return True
    return commands.check(predicate)

def can_moderate(user: discord.Member, moderator: discord.Member) -> bool:
    """Check if moderator can moderate the user"""
    if user == user.guild.owner:
        return False
    if user.top_role >= moderator.top_role:
        return False
    return True
