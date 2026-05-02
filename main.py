"""
Discord Moderation Bot
A complete moderation bot with ban, kick, mute, and warning system
"""
import discord
from discord.ext import commands
import config
from utils.database import init_db
from utils.embed import create_embed
from utils.permissions import get_permission_level
import os

# Create bot instance
intents = discord.Intents.default()
intents.message_content = True  # Required for prefix commands
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix=config.PREFIX, intents=intents, help_command=None)
bot.remove_command('help')

def build_embed(title: str, description: str, color: int, fields: list = None, thumbnail_url: str = None):
    embed = create_embed(title=title, description=description, color=color, footer="Discord Moderation System", thumbnail_url=thumbnail_url)
    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
    return embed

@bot.command(name='help')
async def help_command(ctx, section: str = None):
    user_level = await get_permission_level(ctx.author)
    
    if section is None:
        fields = []
        
        # Always show basic commands for level 1+
        if user_level >= 1:
            fields.append(("Communauté", "!snipe\n!pic [@user]", False))
        
        # Moderation commands for level 2+
        if user_level >= 2:
            fields.append(("Modération", "!kick @user [raison]\n!ban @user [raison]\n!warn @user [raison]\n!mute @user [durée] [raison]\n!unmute @user\n!warnings [@user]\n!clearwarnings @user", False))
        
        # Manager commands for level 3+
        if user_level >= 3:
            fields.append(("Censure", "!wordban add <mot>\n!wordban remove <mot>\n!wordban list", False))
            fields.append(("Tickets", "!ticket create\n!ticket close\n!ticket setup #category", False))
            fields.append(("HardMod", "!massrole @role\n!massmute @role\n!massban @role\n!moveall #voice\n!mutegroup #voice\n!freeze #channel\n!unfreeze #channel", False))
        
        # Admin commands for level 4
        if user_level >= 4:
            fields.append(("Administration", "!blacklist add/remove/list @user [raison]\n!perm set/check/remove @user [1-4]\n!permconfig set/show !commande niveau\n!log set/show/off #channel", False))
        
        embed = build_embed(
            title="Commandes disponibles",
            description=f"Utilise `!help <section>` pour plus de détails.\nVotre niveau de permission : {user_level} ({config.LEVEL_NAMES.get(user_level, 'Inconnu')})",
            color=config.COLOR_INFO,
            fields=fields
        )
        return await ctx.send(embed=embed)

    section = section.lower()
    if section == 'moderation' and user_level >= 2:
        embed = build_embed(
            title="Modération",
            description="Commandes de modération principales.",
            color=config.COLOR_INFO,
            fields=[
                ("kick", "!kick @user [raison]", True),
                ("ban", "!ban @user [raison]", True),
                ("warn", "!warn @user [raison]", True),
                ("mute", "!mute @user [durée] [raison]", True),
                ("unmute", "!unmute @user", True),
                ("warnings", "!warnings [@user]", True),
                ("clearwarnings", "!clearwarnings @user", True)
            ]
        )
    elif section == 'administration' and user_level >= 4:
        embed = build_embed(
            title="Administration",
            description="Commandes d'administration et permissions.",
            color=config.COLOR_INFO,
            fields=[
                ("blacklist", "!blacklist add/remove/list", False),
                ("perm", "!perm set/check/remove", False),
                ("permconfig", "!permconfig set/show", False),
                ("log", "!log set/show/off #channel", False)
            ]
        )
    elif section == 'wordban' and user_level >= 3:
        embed = build_embed(
            title="Censure",
            description="Gestion des mots bannis.",
            color=config.COLOR_INFO,
            fields=[
                ("add", "!wordban add <mot>", False),
                ("remove", "!wordban remove <mot>", False),
                ("list", "!wordban list", False)
            ]
        )
    elif section == 'tickets' and user_level >= 3:
        embed = build_embed(
            title="Tickets",
            description="Gestion des tickets.",
            color=config.COLOR_INFO,
            fields=[
                ("create", "!ticket create", False),
                ("close", "!ticket close", False),
                ("setup", "!ticket setup #category", False)
            ]
        )
    elif section == 'group' and user_level >= 3:
        embed = build_embed(
            title="HardMod",
            description="Commandes de rôle et vocal.",
            color=config.COLOR_INFO,
            fields=[
                ("massrole", "!massrole @role", False),
                ("massban", "!massban @role", False),
                ("massmute", "!massmute @role", False),
                ("moveall", "!moveall #voice", False),
                ("mutegroup", "!mutegroup #voice", False),
                ("freeze", "!freeze #channel", False),
                ("unfreeze", "!unfreeze #channel", False)
            ]
        )
    elif section == 'utilitaires' and user_level >= 1:
        embed = build_embed(
            title="Communauté",
            description="Commandes utilitaires.",
            color=config.COLOR_INFO,
            fields=[
                ("snipe", "!snipe", False),
                ("pic", "!pic [@user]", False)
            ]
        )
    else:
        embed = build_embed("Section inconnue ou accès refusé", "Sections valides selon votre niveau : " + ", ".join([s for s in ["utilitaires", "moderation", "wordban", "tickets", "group", "administration"] if (s == "utilitaires" and user_level >= 1) or (s == "moderation" and user_level >= 2) or (s in ["wordban", "tickets", "group"] and user_level >= 3) or (s == "administration" and user_level >= 4)]), config.COLOR_ERROR)
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    """Bot ready event"""
    print(f"Bot logged in as {bot.user}")
    print(f"Prefix: {config.PREFIX}")
    print(f"Ready to moderate! Use {config.PREFIX} to access commands")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{config.PREFIX}help | Moderation Bot"
        )
    )

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.CheckFailure):
        embed = discord.Embed(
            title="Permission refusée",
            description="Vous n'avez pas la permission requise pour utiliser cette commande.",
            color=config.COLOR_ERROR
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="Permission refusée",
            description="Vous n'avez pas la permission requise pour utiliser cette commande.",
            color=config.COLOR_ERROR
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="Argument manquant",
            description=f"Argument requis manquant : {error.param.name}",
            color=config.COLOR_ERROR
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(
            title="Commande introuvable",
            description="Cette commande n'existe pas. Utilisez `!help` pour voir la liste.",
            color=config.COLOR_ERROR
        )
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="Erreur",
            description=f"Une erreur est survenue : {str(error)}",
            color=config.COLOR_ERROR
        )
        await ctx.send(embed=embed)

async def load_cogs():
    """Load all cogs from the cogs directory"""
    cogs_dir = "cogs"
    for filename in os.listdir(cogs_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            cog_name = filename[:-3]
            try:
                await bot.load_extension(f"cogs.{cog_name}")
                print(f"Loaded cog: {cog_name}")
            except Exception as e:
                print(f"Failed to load cog {cog_name}: {e}")

async def main():
    """Main function to start the bot"""
    async with bot:
        # Initialize database
        await init_db()
        print("Database initialized")
        
        # Load cogs
        await load_cogs()
        
        # Start bot
        try:
            await bot.start(config.TOKEN)
        except ValueError:
            print("Error: No token found. Please set DISCORD_TOKEN in .env file")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
