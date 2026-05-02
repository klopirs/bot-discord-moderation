"""
Moderation and utility commands cog
"""
import re
import discord
from discord.ext import commands
from datetime import timedelta
import config
from utils.permissions import can_moderate, permission_level, has_command_permission, get_permission_level
from utils.database import (
    add_case, add_warning, get_warnings, clear_warnings, get_user_warnings,
    add_blacklist, remove_blacklist, list_blacklist,
    set_user_permission, get_user_permission_level, remove_user_permission,
    set_command_permission, get_command_permission_level,
    add_snipe, get_snipe,
    create_ticket, close_ticket, get_ticket,
    add_banned_word, remove_banned_word, list_banned_words,
    set_guild_setting, get_guild_setting, remove_guild_setting,
    add_action_log
)
from utils.embed import create_embed


class Moderation(commands.Cog):
    """Moderation and utility commands."""

    def __init__(self, bot):
        self.bot = bot

    def build_embed(self, title: str, description: str, color: int, fields: list = None, thumbnail: str = None):
        embed = create_embed(title=title, description=description, color=color, footer="Discord Moderation System", thumbnail_url=thumbnail)
        if fields:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
        return embed

    def _contains_banned_word(self, content: str, banned_words: list[str]) -> str | None:
        lower = content.lower()
        for word in banned_words:
            if re.search(rf"\b{re.escape(word)}\b", lower):
                return word
        return None

    def _command_target_text(self, ctx) -> str:
        args = []
        for arg in ctx.args[1:]:
            if isinstance(arg, discord.Member):
                args.append(arg.mention)
            elif isinstance(arg, discord.Role):
                args.append(arg.name)
            elif isinstance(arg, (discord.TextChannel, discord.VoiceChannel)):
                args.append(arg.mention)
            else:
                args.append(str(arg))
        return ' '.join(args).strip()

    async def log_action(self, guild: discord.Guild, action: str, moderator: discord.Member | None = None, target: discord.Member | None = None, details: str | None = None, exclude_channel_id: int | None = None):
        channel_id = await get_guild_setting(guild.id, 'log_channel')
        await add_action_log(guild.id, action, target.id if target else None, moderator.id if moderator else None, details)
        if not channel_id or (exclude_channel_id and int(channel_id) == exclude_channel_id):
            return
        channel = guild.get_channel(int(channel_id))
        if not channel:
            return
        embed = self.build_embed(
            title=f"Log - {action}",
            description=details or f"Action exécutée par {moderator.mention if moderator else 'Système'}.",
            color=config.COLOR_INFO,
            fields=[
                ("Action", action, True),
                ("Par", moderator.mention if moderator else 'Système', True),
                ("Cible", target.mention if target else 'Aucune', True)
            ]
        )
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.guild:
            banned_entries = await list_banned_words(message.guild.id)
            if banned_entries:
                banned_words = [row[0] for row in banned_entries]
                found_word = self._contains_banned_word(message.content or '', banned_words)
                if found_word:
                    await message.delete()
                    await self.log_action(
                        message.guild,
                        action="Mot bannis détecté",
                        moderator=message.author,
                        details=f"Message supprimé contenant `{found_word}` dans {message.channel.mention}."
                    )
                    return
        # Note: process_commands removed to prevent duplicate command execution
        # If commands stop working, restore: await self.bot.process_commands(message)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.guild is None or message.author.bot:
            return
        attachments = ", ".join(a.url for a in message.attachments) if message.attachments else None
        await add_snipe(message.guild.id, message.channel.id, message.author.id, message.content, attachments)

    @commands.command(name='kick')
    @permission_level(2)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Aucune raison fournie"):
        if not can_moderate(member, ctx.author):
            return await ctx.send(self.build_embed("Impossible", f"Vous ne pouvez pas kicker {member.mention}", config.COLOR_ERROR))
        try:
            await member.kick(reason=reason)
            await add_case(ctx.guild.id, "KICK", member.id, ctx.author.id, reason)
            await ctx.send(self.build_embed("Membre expulsé", f"{member.mention} a été expulsé", config.COLOR_SUCCESS, fields=[("Raison", reason, False), ("Modérateur", ctx.author.mention, False)], thumbnail=member.avatar.url if member.avatar else None))
            await self.log_action(ctx.guild, action="Kick", moderator=ctx.author, target=member, details=reason, exclude_channel_id=ctx.channel.id)
        except discord.Forbidden:
            await ctx.send(self.build_embed("Erreur", "Je n'ai pas la permission de kicker ce membre.", config.COLOR_ERROR))

    @commands.command(name='ban')
    @permission_level(2)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Aucune raison fournie"):
        if not can_moderate(member, ctx.author):
            return await ctx.send(self.build_embed("Impossible", f"Vous ne pouvez pas bannir {member.mention}", config.COLOR_ERROR))
        try:
            await member.ban(reason=reason)
            await add_case(ctx.guild.id, "BAN", member.id, ctx.author.id, reason)
            await ctx.send(self.build_embed("Membre banni", f"{member.mention} a été banni", config.COLOR_SUCCESS, fields=[("Raison", reason, False), ("Modérateur", ctx.author.mention, False)], thumbnail=member.avatar.url if member.avatar else None))
            await self.log_action(ctx.guild, action="Ban", moderator=ctx.author, target=member, details=reason, exclude_channel_id=ctx.channel.id)
        except discord.Forbidden:
            await ctx.send(self.build_embed("Erreur", "Je n'ai pas la permission de bannir ce membre.", config.COLOR_ERROR))

    @commands.command(name='warn')
    @permission_level(2)
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Aucune raison fournie"):
        if not can_moderate(member, ctx.author):
            return await ctx.send(self.build_embed("Impossible", f"Vous ne pouvez pas warn {member.mention}", config.COLOR_ERROR))
        await add_warning(member.id, ctx.guild.id, ctx.author.id, reason)
        await add_case(ctx.guild.id, "WARN", member.id, ctx.author.id, reason)
        warnings = await get_warnings(member.id, ctx.guild.id)
        await ctx.send(self.build_embed("Avertissement ajouté", f"{member.mention} a été averti", config.COLOR_WARNING, fields=[("Raison", reason, False), ("Total", f"{warnings}/{config.MAX_WARNINGS}", False), ("Modérateur", ctx.author.mention, False)], thumbnail=member.avatar.url if member.avatar else None))
        await self.log_action(ctx.guild, action="Warn", moderator=ctx.author, target=member, details=reason, exclude_channel_id=ctx.channel.id)
        if warnings >= config.MAX_WARNINGS:
            try:
                await member.ban(reason=f"Atteint {config.MAX_WARNINGS} avertissements")
                await add_case(ctx.guild.id, "AUTO_BAN", member.id, self.bot.user.id, f"Atteint {config.MAX_WARNINGS} avertissements")
                await ctx.send(self.build_embed("Auto-ban", f"{member.mention} a été banni automatiquement.", config.COLOR_ERROR))
                await self.log_action(ctx.guild, action="Auto-ban", moderator=self.bot.user, target=member, details=f"Atteint {config.MAX_WARNINGS} avertissements", exclude_channel_id=ctx.channel.id)
            except discord.Forbidden:
                pass

    @commands.command(name='mute')
    @permission_level(2)
    async def mute(self, ctx: commands.Context, member: discord.Member, duration: str = "10m", *, reason: str = "Aucune raison fournie"):
        if not can_moderate(member, ctx.author):
            return await ctx.send(self.build_embed("Impossible", f"Vous ne pouvez pas mute {member.mention}", config.COLOR_ERROR))
        try:
            time_unit = duration[-1]
            time_value = int(duration[:-1])
            if time_unit == 'm':
                duration_obj = timedelta(minutes=time_value)
            elif time_unit == 'h':
                duration_obj = timedelta(hours=time_value)
            elif time_unit == 'd':
                duration_obj = timedelta(days=time_value)
            else:
                duration_obj = timedelta(minutes=10)
        except Exception:
            duration_obj = timedelta(minutes=10)
        try:
            await member.timeout(duration=duration_obj, reason=reason)
            await add_case(ctx.guild.id, "MUTE", member.id, ctx.author.id, reason)
            await ctx.send(self.build_embed("Membre mute", f"{member.mention} est maintenant mute", config.COLOR_INFO, fields=[("Durée", str(duration_obj), False), ("Raison", reason, False), ("Modérateur", ctx.author.mention, False)], thumbnail=member.avatar.url if member.avatar else None))
            await self.log_action(ctx.guild, action="Mute", moderator=ctx.author, target=member, details=f"{reason} ({duration})", exclude_channel_id=ctx.channel.id)
        except discord.Forbidden:
            await ctx.send(self.build_embed("Erreur", "Je n'ai pas la permission de mute ce membre.", config.COLOR_ERROR))

    @commands.command(name='unmute')
    @permission_level(2)
    async def unmute(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Aucune raison fournie"):
        try:
            await member.timeout(duration=None, reason=reason)
            await add_case(ctx.guild.id, "UNMUTE", member.id, ctx.author.id, reason)
            await ctx.send(self.build_embed("Membre unmute", f"{member.mention} peut de nouveau parler", config.COLOR_SUCCESS, fields=[("Raison", reason, False), ("Modérateur", ctx.author.mention, False)], thumbnail=member.avatar.url if member.avatar else None))
            await self.log_action(ctx.guild, action="Unmute", moderator=ctx.author, target=member, details=reason, exclude_channel_id=ctx.channel.id)
        except discord.Forbidden:
            await ctx.send(self.build_embed("Erreur", "Je n'ai pas la permission de unmute ce membre.", config.COLOR_ERROR))

    @commands.command(name='warnings')
    async def warnings(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        warnings = await get_user_warnings(target.id, ctx.guild.id)
        embed = self.build_embed("Avertissements", f"Total : {len(warnings)}", config.COLOR_INFO, thumbnail=target.avatar.url if target.avatar else None)
        if warnings:
            for idx, warning in enumerate(warnings[:8], 1):
                embed.add_field(name=f"Avertissement #{idx}", value=f"Raison: {warning[4]}\nDate: {warning[5]}", inline=False)
        else:
            embed.description = f"{target.mention} n'a aucun avertissement"
        await ctx.send(embed=embed)

    @commands.command(name='clearwarnings')
    @permission_level(2)
    async def clearwarnings(self, ctx: commands.Context, member: discord.Member):
        await clear_warnings(member.id, ctx.guild.id)
        await ctx.send(self.build_embed("Avertissements effacés", f"Tous les avertissements de {member.mention} ont été supprimés.", config.COLOR_SUCCESS, fields=[("Modérateur", ctx.author.mention, False)], thumbnail=member.avatar.url if member.avatar else None))
        await self.log_action(ctx.guild, action="Clear warnings", moderator=ctx.author, target=member, exclude_channel_id=ctx.channel.id)

    @commands.command(name='snipe')
    @permission_level(1)
    async def snipe(self, ctx: commands.Context):
        snipe_data = await get_snipe(ctx.guild.id, ctx.channel.id)
        if not snipe_data:
            return await ctx.send(self.build_embed("Rien à snipe", "Aucun message supprimé récemment dans ce salon.", config.COLOR_WARNING))
        user_id, content, attachments, timestamp = snipe_data
        user = ctx.guild.get_member(user_id)
        embed = self.build_embed("Dernier message supprimé", content or "Aucun texte à afficher.", config.COLOR_INFO, fields=[("Auteur", user.mention if user else f"<@{user_id}>", False), ("Supprimé le", timestamp, False)])
        if attachments:
            embed.add_field(name="Pièces jointes", value=attachments, inline=False)
        await ctx.send(embed=embed)

    @commands.group(name='blacklist', invoke_without_command=True)
    @permission_level(3)
    async def blacklist(self, ctx: commands.Context):
        await ctx.send(self.build_embed("Utilisation : !blacklist add/remove/list", "Utilisez une sous-commande valide.", config.COLOR_WARNING))

    @blacklist.command(name='add')
    @permission_level(3)
    async def blacklist_add(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Aucune raison fournie"):
        await add_blacklist(member.id, ctx.guild.id, ctx.author.id, reason)
        await ctx.send(self.build_embed("Blacklist ajouté", f"{member.mention} est maintenant blacklisté.", config.COLOR_SUCCESS, fields=[("Raison", reason, False), ("Par", ctx.author.mention, False)]))
        await self.log_action(ctx.guild, action="Blacklist add", moderator=ctx.author, target=member, details=reason, exclude_channel_id=ctx.channel.id)

    @blacklist.command(name='remove')
    @permission_level(4)
    async def blacklist_remove(self, ctx: commands.Context, member: discord.Member):
        await remove_blacklist(member.id, ctx.guild.id)
        await ctx.send(self.build_embed("Blacklist retiré", f"{member.mention} n'est plus blacklisté.", config.COLOR_SUCCESS, fields=[("Par", ctx.author.mention, False)]))
        await self.log_action(ctx.guild, action="Blacklist remove", moderator=ctx.author, target=member, exclude_channel_id=ctx.channel.id)

    @blacklist.command(name='list')
    @permission_level(3)
    async def blacklist_list(self, ctx: commands.Context):
        rows = await list_blacklist(ctx.guild.id)
        if not rows:
            return await ctx.send(self.build_embed("Blacklist vide", "Aucun utilisateur blacklisté.", config.COLOR_SUCCESS))
        value = "\n".join([f"<@{row[0]}> - {row[1] or 'Aucune raison'}" for row in rows])
        await ctx.send(self.build_embed("Blacklist", value, config.COLOR_INFO))

    @commands.group(name='wordban', invoke_without_command=True)
    @permission_level(3)
    async def wordban(self, ctx: commands.Context):
        await ctx.send(self.build_embed("Utilisation : !wordban add/remove/list", "Utilisez une sous-commande valide.", config.COLOR_WARNING))

    @wordban.command(name='add')
    @permission_level(3)
    async def wordban_add(self, ctx: commands.Context, word: str):
        await add_banned_word(ctx.guild.id, word, ctx.author.id)
        await ctx.send(self.build_embed("Mot ajouté", f"Le mot `{word}` est maintenant surveillé.", config.COLOR_SUCCESS, fields=[("Par", ctx.author.mention, False)]))

    @wordban.command(name='remove')
    @permission_level(4)
    async def wordban_remove(self, ctx: commands.Context, word: str):
        await remove_banned_word(ctx.guild.id, word)
        await ctx.send(self.build_embed("Mot retiré", f"Le mot `{word}` n'est plus surveillé.", config.COLOR_SUCCESS, fields=[("Par", ctx.author.mention, False)]))

    @wordban.command(name='list')
    @permission_level(3)
    async def wordban_list(self, ctx: commands.Context):
        rows = await list_banned_words(ctx.guild.id)
        if not rows:
            return await ctx.send(self.build_embed("Aucun mot", "Aucun mot interdit n'est configuré.", config.COLOR_SUCCESS))
        value = "\n".join([f"`{row[0]}` ajouté par <@{row[1]}>" for row in rows])
        await ctx.send(self.build_embed("Mots bannis", value, config.COLOR_INFO))

    @commands.group(name='log', invoke_without_command=True)
    @permission_level(3)
    async def log(self, ctx: commands.Context):
        await ctx.send(self.build_embed("Utilisation : !log set/show/off #channel", "Utilisez une sous-commande valide.", config.COLOR_WARNING))

    @log.command(name='set')
    @permission_level(4)
    async def log_set(self, ctx: commands.Context, channel: discord.TextChannel):
        await set_guild_setting(ctx.guild.id, 'log_channel', str(channel.id))
        await ctx.send(self.build_embed("Canal de logs défini", f"Les actions seront envoyées dans {channel.mention}.", config.COLOR_SUCCESS))

    @log.command(name='show')
    @permission_level(3)
    async def log_show(self, ctx: commands.Context):
        channel_id = await get_guild_setting(ctx.guild.id, 'log_channel')
        if not channel_id:
            return await ctx.send(self.build_embed("Aucun canal", "Aucun canal de logs n'est configuré.", config.COLOR_WARNING))
        channel = ctx.guild.get_channel(int(channel_id))
        await ctx.send(self.build_embed("Canal de logs", f"Les actions seront envoyées dans {channel.mention if channel else 'un canal inconnu'}.", config.COLOR_INFO))

    @log.command(name='off')
    @permission_level(4)
    async def log_off(self, ctx: commands.Context):
        await remove_guild_setting(ctx.guild.id, 'log_channel')
        await ctx.send(self.build_embed("Logs désactivés", "Aucun canal de logs n'est configuré.", config.COLOR_SUCCESS))

    @commands.group(name='perm', invoke_without_command=True)
    @permission_level(3)
    async def perm(self, ctx: commands.Context):
        await ctx.send(self.build_embed("Utilisation : !perm set/check/remove", "Utilisez une sous-commande valide.", config.COLOR_WARNING))

    @perm.command(name='set')
    @permission_level(3)
    async def perm_set(self, ctx: commands.Context, member: discord.Member, level: int):
        level = max(1, min(4, level))
        await set_user_permission(member.id, ctx.guild.id, level)
        await ctx.send(self.build_embed("Permission définie", f"{member.mention} a maintenant le niveau {level}.", config.COLOR_SUCCESS))

    @perm.command(name='check')
    @permission_level(2)
    async def perm_check(self, ctx: commands.Context, member: discord.Member):
        custom_level = await get_user_permission_level(member.id, ctx.guild.id)
        effective = custom_level or await get_permission_level(member)
        await ctx.send(self.build_embed("Niveau de permission", f"{member.mention} est niveau {effective}.", config.COLOR_INFO))

    @perm.command(name='remove')
    @permission_level(4)
    async def perm_remove(self, ctx: commands.Context, member: discord.Member):
        await remove_user_permission(member.id, ctx.guild.id)
        await ctx.send(self.build_embed("Permission retirée", f"Permission personnalisée supprimée pour {member.mention}.", config.COLOR_SUCCESS))

    @commands.group(name='permconfig', invoke_without_command=True)
    @permission_level(4)
    async def permconfig(self, ctx: commands.Context):
        await ctx.send(self.build_embed("Utilisation : !permconfig set/show", "Utilisez une sous-commande valide.", config.COLOR_WARNING))

    @permconfig.command(name='set')
    @permission_level(4)
    async def permconfig_set(self, ctx: commands.Context, command_name: str, level: int):
        level = max(1, min(4, level))
        await set_command_permission(ctx.guild.id, command_name, level)
        await ctx.send(self.build_embed("Commande configurée", f"{command_name} nécessite maintenant le niveau {level}.", config.COLOR_SUCCESS))

    @permconfig.command(name='show')
    @permission_level(3)
    async def permconfig_show(self, ctx: commands.Context, command_name: str | None = None):
        if command_name:
            level = await get_command_permission_level(ctx.guild.id, command_name) or config.DEFAULT_COMMAND_LEVELS.get(command_name, 1)
            await ctx.send(self.build_embed("Permission de commande", f"{command_name} nécessite le niveau {level}.", config.COLOR_INFO))
            return
        lines = []
        for command_name, default_level in config.DEFAULT_COMMAND_LEVELS.items():
            custom = await get_command_permission_level(ctx.guild.id, command_name)
            effective = custom or default_level
            lines.append(f"`{command_name}`: {effective}")
        await ctx.send(self.build_embed("Permissions de commandes", "\n".join(lines[:20]), config.COLOR_INFO))

    @commands.group(name='ticket', invoke_without_command=True)
    @permission_level(2)
    async def ticket(self, ctx: commands.Context):
        await ctx.send(self.build_embed("Utilisation : !ticket create/close/setup", "Utilisez une sous-commande valide.", config.COLOR_WARNING))

    @ticket.command(name='create')
    @permission_level(2)
    async def ticket_create(self, ctx: commands.Context):
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await ctx.guild.create_text_channel(f"ticket-{ctx.author.name}", overwrites=overwrites)
        await create_ticket(ctx.guild.id, channel.id, ctx.author.id)
        await ctx.send(self.build_embed("Ticket créé", f"Salon de ticket créé : {channel.mention}", config.COLOR_SUCCESS))

    @ticket.command(name='close')
    @permission_level(2)
    async def ticket_close(self, ctx: commands.Context):
        ticket = await get_ticket(ctx.channel.id, ctx.guild.id)
        if not ticket:
            return await ctx.send(self.build_embed("Erreur", "Ce salon n'est pas un ticket.", config.COLOR_ERROR))
        await close_ticket(ctx.channel.id, ctx.guild.id)
        await ctx.channel.delete()

    @ticket.command(name='setup')
    @permission_level(3)
    async def ticket_setup(self, ctx: commands.Context, category: discord.CategoryChannel):
        await ctx.send(self.build_embed("Ticket configuré", f"Utilisez !ticket create pour ouvrir un ticket dans cette catégorie.", config.COLOR_SUCCESS))

    @commands.command(name='embed')
    @permission_level(3)
    async def embed_command(self, ctx: commands.Context, title: str, *, description: str):
        await ctx.send(self.build_embed(title, description, config.COLOR_HIGHLIGHT))

    @commands.command(name='massrole')
    @permission_level(4)
    async def massrole(self, ctx: commands.Context, role: discord.Role):
        members = [m for m in ctx.guild.members if role not in m.roles and not m.bot]
        count = 0
        for member in members:
            try:
                await member.add_roles(role, reason="Mass role assigné")
                count += 1
            except discord.Forbidden:
                continue
        await ctx.send(self.build_embed("Mass role", f"{count} membres ont reçu le rôle {role.name}.", config.COLOR_SUCCESS))

    @commands.command(name='massban')
    @permission_level(4)
    async def massban(self, ctx: commands.Context, role: discord.Role):
        members = [m for m in ctx.guild.members if role in m.roles and not m.bot]
        count = 0
        for member in members:
            try:
                await member.ban(reason="Mass ban")
                count += 1
            except discord.Forbidden:
                continue
        await ctx.send(self.build_embed("Mass ban", f"{count} membres bannis.", config.COLOR_ERROR))

    @commands.command(name='massmute')
    @permission_level(4)
    async def massmute(self, ctx: commands.Context, role: discord.Role, duration: str = "10m", *, reason: str = "Aucune raison fournie"):
        try:
            time_unit = duration[-1]
            time_value = int(duration[:-1])
            if time_unit == 'm':
                duration_obj = timedelta(minutes=time_value)
            elif time_unit == 'h':
                duration_obj = timedelta(hours=time_value)
            elif time_unit == 'd':
                duration_obj = timedelta(days=time_value)
            else:
                duration_obj = timedelta(minutes=10)
        except Exception:
            duration_obj = timedelta(minutes=10)
        members = [m for m in ctx.guild.members if role in m.roles and not m.bot]
        count = 0
        for member in members:
            try:
                await member.timeout(duration=duration_obj, reason=reason)
                count += 1
            except discord.Forbidden:
                continue
        await ctx.send(self.build_embed("Mass mute", f"{count} membres ont été mute pendant {duration}.", config.COLOR_INFO))

    @commands.command(name='moveall')
    @permission_level(4)
    async def moveall(self, ctx: commands.Context, destination: discord.VoiceChannel):
        count = 0
        for member in ctx.guild.members:
            if member.voice and member.voice.channel != destination and not member.bot:
                try:
                    await member.move_to(destination, reason="Move all command")
                    count += 1
                except discord.Forbidden:
                    continue
        await ctx.send(self.build_embed("Move all", f"{count} membres déplacés vers {destination.name}.", config.COLOR_SUCCESS))

    @commands.command(name='mutegroup')
    @permission_level(4)
    async def mutegroup(self, ctx: commands.Context, voice_channel: discord.VoiceChannel, duration: str = "10m", *, reason: str = "Aucune raison fournie"):
        try:
            time_unit = duration[-1]
            time_value = int(duration[:-1])
            if time_unit == 'm':
                duration_obj = timedelta(minutes=time_value)
            elif time_unit == 'h':
                duration_obj = timedelta(hours=time_value)
            elif time_unit == 'd':
                duration_obj = timedelta(days=time_value)
            else:
                duration_obj = timedelta(minutes=10)
        except Exception:
            duration_obj = timedelta(minutes=10)
        count = 0
        for member in voice_channel.members:
            if not member.bot:
                try:
                    await member.timeout(duration=duration_obj, reason=reason)
                    count += 1
                except discord.Forbidden:
                    continue
        await ctx.send(self.build_embed("Mute groupe", f"{count} membres mute dans {voice_channel.name}.", config.COLOR_INFO))

    @commands.command(name='freeze')
    @permission_level(3)
    async def freeze(self, ctx: commands.Context, channel: discord.TextChannel = None):
        target = channel or ctx.channel
        overwrite = target.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await target.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(self.build_embed("Salon freeze", f"{target.mention} est maintenant en freeze.", config.COLOR_WARNING))

    @commands.command(name='unfreeze')
    @permission_level(3)
    async def unfreeze(self, ctx: commands.Context, channel: discord.TextChannel = None):
        target = channel or ctx.channel
        overwrite = target.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await target.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(self.build_embed("Salon unfreeze", f"{target.mention} peut de nouveau envoyer des messages.", config.COLOR_SUCCESS))

    @commands.command(name='pic')
    @permission_level(1)
    async def pic(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        embed = self.build_embed("Photo de profil", f"Photo de profil de {target.mention}", config.COLOR_INFO, thumbnail=target.avatar.url if target.avatar else target.default_avatar.url)
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
