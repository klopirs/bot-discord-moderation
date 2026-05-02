"""
Information and utility commands
"""
import discord
from discord.ext import commands
import config
from utils.database import get_cases

class Info(commands.Cog):
    """Information commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='listcommands')
    async def listcommands(self, ctx):
        """Display help information"""
        embed = discord.Embed(
            title="Bot Commands",
            description="Complete list of moderation commands",
            color=config.COLOR_INFO
        )
        
        embed.add_field(
            name="Moderation",
            value="""
`!kick @user [reason]` - Kick a user
`!ban @user [reason]` - Ban a user
`!warn @user [reason]` - Warn a user
`!mute @user [duration] [reason]` - Mute a user (e.g., 10m, 1h)
`!unmute @user [reason]` - Unmute a user
`!warnings [@user]` - Check warnings
`!clearwarnings @user` - Clear all warnings
`!cases [@user]` - Show moderation cases
            """,
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='cases')
    async def cases(self, ctx, member: discord.Member = None):
        """Show moderation cases"""
        cases = await get_cases(ctx.guild.id, member.id if member else None)
        
        target_text = member.mention if member else "all members"
        embed = discord.Embed(
            title=f"Moderation Cases ({target_text})",
            description=f"Total cases: {len(cases)}",
            color=config.COLOR_INFO
        )
        
        if cases:
            for idx, case in enumerate(cases[:10], 1):  # Show last 10 cases
                embed.add_field(
                    name=f"Case #{idx} - {case[2]}",  # action
                    value=f"User: <@{case[3]}>\nReason: {case[5]}\nDate: {case[6]}",
                    inline=False
                )
        else:
            embed.description = f"No cases found"
        
        await ctx.send(embed=embed)
    
    @commands.command(name='ping')
    async def ping(self, ctx):
        """Check bot latency"""
        embed = discord.Embed(
            title="Pong!",
            description=f"Latency: {round(self.bot.latency * 1000)}ms",
            color=config.COLOR_SUCCESS
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Info(bot))
