import logging

import discord
import requests
from bs4 import BeautifulSoup
from discord.ext import commands
from discord.ext.commands import Bot, Cog

import config
from utils import embeds
from utils.record import record_usage
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option, create_permission
from discord_slash.model import SlashCommandPermissionType

log = logging.getLogger(__name__)

class General(Cog):
    """ General Commands Cog """

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.before_invoke(record_usage)
    @commands.bot_has_permissions(embed_links=True)
    @cog_ext.cog_slash(
        name="pfp", 
        description="Gets the members profile picture",
        guild_ids=[config.guild_id]
    )
    async def pfp(self, ctx: SlashContext, user: discord.User = None):
        """ Returns the profile picture of the invoker or the mentioned user. """
        await ctx.defer()

        user = user or ctx.author

        # If we received an int instead of a discord.Member, the user is not in the server.
        if isinstance(user, int):
            user = await self.bot.fetch_user(user)

        if ctx.author:
            embed = embeds.make_embed(ctx=ctx)

        if user:
            embed = embeds.make_embed()
            embed.set_author(icon_url=user.avatar_url, name=str(user))

        embed.set_image(url=user.avatar_url)
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="population", 
        description="Gets the current server population count",
        guild_ids=[config.guild_id],
        default_permission=False,
        permissions={
            config.guild_id: [
                create_permission(config.role_staff, SlashCommandPermissionType.ROLE, True),
                create_permission(config.role_trial_mod, SlashCommandPermissionType.ROLE, True)
            ]
        }
    )
    async def count(self, ctx: SlashContext):
        """Returns the current guild member count."""
        await ctx.defer()
        await ctx.send(ctx.guild.member_count)

    
    @commands.before_invoke(record_usage)
    @cog_ext.cog_slash(
        name="vote", 
        description="Adds the vote reactions to a message",
        guild_ids=[config.guild_id],
        options=[
            create_option(
                name="message",
                description="The ID for the target message",
                option_type=3,
                required=False
            ),
        ],
        default_permission=False,
        permissions={
            config.guild_id: [
                create_permission(config.role_staff, SlashCommandPermissionType.ROLE, True),
                create_permission(config.role_trial_mod, SlashCommandPermissionType.ROLE, True)
            ]
        }
    )
    async def vote(self, ctx, message: discord.Message = None):
        """ Add vote reactions to a message. """
        await ctx.defer()
        
        if message:
            message = await ctx.channel.fetch_message(message)

        if not message:
            messages = await ctx.channel.history(limit=1).flatten()
            message = messages[0]

        await message.add_reaction(config.emote_yes)
        await message.add_reaction(config.emote_no)
        
        # We need to send *something* so the bot doesn't return "This interaction failed"
        delete = await ctx.send("** **")
        await delete.delete()

    @commands.before_invoke(record_usage)
    @cog_ext.cog_slash(
        name="nyaa", 
        description="Lookup for Nyaa torrent entry",
        guild_ids=[config.guild_id],
        options=[
            create_option(
                name="id",
                description="The ID of the torrent found at the end of the URL, https://nyaa.si/view/######",
                option_type=4,
                required=True
            ),
        ],
        default_permission=True
    )
    async def nyaa(self, ctx, torrent: int):
        """ Add vote reactions to a message. """
        await ctx.defer()
        
        r = requests.get(f"https://nyaa.si/view/{torrent}")

        # Check to see if the torrent exists and throw an error if it doesn't.
        if r.status_code == 404:
            await embeds.error_message(ctx=ctx, description=f"No torrent exists at that Nyaa ID.")
            return

        # Check to see if the site is having downtime issues, it should return HTTP 200 if all is well.
        if r.status_code != 200:
            await embeds.error_message(ctx=ctx, description=f"An iss/ue occurred on Nyaa's end. Try again later.")
            return
        
        # Setup the BeautifulSoup parser and scrape the torrent title.
        soup = BeautifulSoup(r.text, "html.parser")
        title = ' '.join(soup.select("h3.panel-title")[0].get_text().split())

        embed = embeds.make_embed(
            title=title,
            thumbnail_url="https://pbs.twimg.com/profile_images/865586129059201024/fH1dmIuo_400x400.jpg",
            color=0x0284fe
        )

        # Apparently ' '.join(.split()) is the easiest way to strip away \t, \n, etc...
        submitter = ' '.join(soup.select(".panel-body > div:nth-of-type(2) > .col-md-5")[0].get_text().split())
        date = ' '.join(soup.select(".panel-body > div:nth-of-type(1) > .col-md-5")[1].get_text().split())
        size = ' '.join(soup.select(".panel-body > div:nth-of-type(4) > .col-md-5")[0].get_text().split())
        seeders = ' '.join(soup.select(".panel-body > div:nth-of-type(2) > .col-md-5 > span")[0].get_text().split())
        leechers = ' '.join(soup.select(".panel-body > div:nth-of-type(3) > .col-md-5 > span")[0].get_text().split())
        completed = ' '.join(soup.select(".panel-body > div:nth-of-type(4) > .col-md-5")[1].get_text().split())

        # file_list = soup.find_all("div", {"class": "torrent-file-list panel-body"})[0]
        #file_list = """
        #📁 [Kulot] Turn A Gundam BD Subtitles v0 (Updated)
        # 📁 Fonts (230.7 KiB)
        #  📄 CRONOSPRO-SEMIBOLD.TTF
        #  📄 CRONOSPRO-SEMIBOLDIT.TTF
        # 📁 Subtitles (432.6 KiB)
        #  📄 [EG]Turn-A_Gundam_BD_01(1080p_10bit)(...).ass
        #  📄 [EG]Turn-A_Gundam_BD_02_V2(1080p_10bit)(...).ass
        #  📄 [EG]Turn-A_Gundam_BD_03(1080p_10bit)(...).ass
        #  📄 [EG]Turn-A_Gundam_BD_04(1080p_10bit)(...).ass
        #  📄 [EG]Turn-A_Gundam_BD_05(1080p_10bit)(...).ass
        #  📄 [EG]Turn-A_Gundam_BD_06(1080p_10bit)(...).ass
        #  📄 [EG]Turn-A_Gundam_BD_07(1080p_10bit)(...).ass
        #  ... and 6 more files
        #"""

        embed.add_field(name="Submitter:", value=submitter, inline=True)
        embed.add_field(name="Date:", value=date, inline=True)
        embed.add_field(name="File Size:", value=size, inline=True)

        embed.add_field(name="Seeders:", value=seeders, inline=True)
        embed.add_field(name="Leechers:", value=leechers, inline=True)
        embed.add_field(name="Completed:", value=completed, inline=True)
        
        # embed.add_field(name="File List:", value=file_list, inline=False)

        await ctx.send(embed=embed)
        



def setup(bot: Bot) -> None:
    """ Load the General cog. """
    bot.add_cog(General(bot))
    log.info("Commands loaded: general")
