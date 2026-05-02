"""
Helper utilities for stylized Discord embeds.
"""
import discord
import config


def create_embed(title: str, description: str = None, color: int = config.COLOR_INFO, footer: str = None, thumbnail_url: str = None):
    embed = discord.Embed(title=title, description=description or "", color=color)
    if footer:
        embed.set_footer(text=footer)
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
    return embed
