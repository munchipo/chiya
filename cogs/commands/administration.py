import io
import logging
import textwrap
import traceback
from contextlib import redirect_stdout

import discord
from discord.ext import commands
from discord.ext.commands import Bot, Cog, Context
from discord_slash import ComponentContext
from discord_slash.utils.manage_commands import remove_all_commands
from discord_slash.utils.manage_components import create_select, create_select_option, create_actionrow

from utils import embeds
from utils.config import config
from utils.record import record_usage

# Enabling logs
log = logging.getLogger(__name__)


class AdministrationCog(Cog):
    """Administration Cog Cog"""

    def __init__(self, bot):
        self.bot = bot
        self._last_result = None

    def _cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:-1])

        # remove `foo`
        return content.strip("` \n")

    @commands.before_invoke(record_usage)
    @commands.group(aliases=["u", "ul"])
    async def utilities(self, ctx):
        return

    @commands.is_owner()
    @utilities.command(name="ping")
    async def ping(self, ctx):
        """Returns the Discord WebSocket latency."""
        await ctx.send(f"{round(self.bot.latency * 1000)}ms.")

    @commands.is_owner()
    @utilities.command(name="removecmds")
    async def removecmds(self, ctx):
        await remove_all_commands(bot_id=self.bot.user.id, bot_token=config["bot"]["token"], guild_ids=[config["guild_id"]])

    @commands.is_owner()
    @utilities.command(name="say")
    async def say(self, ctx, *, args):
        """Echos the input argument."""
        await ctx.send(args)

    @commands.is_owner()
    @utilities.command(name="eval")
    async def eval(self, ctx, *, body: str):
        """Evaluates input as Python code."""
        # Required environment variables.
        env = {
            "bot": self.bot,
            "ctx": ctx,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message,
            "embeds": embeds,
            "_": self._last_result,
        }
        # Creating embed.
        embed = discord.Embed(title="Evaluating.", color=0xB134EB)
        env.update(globals())

        # Calling cleanup command to remove the markdown traces.
        body = self._cleanup_code(body)
        embed.add_field(name="Input:", value=f"```py\n{body}\n```", inline=False)
        # Output stream.
        stdout = io.StringIO()

        # Exact code to be compiled.
        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            # Attempting execution
            exec(to_compile, env)
        except Exception as e:
            # In case there's an error, add it to the embed, send and stop.
            errors = f"```py\n{e.__class__.__name__}: {e}\n```"
            embed.add_field(name="Errors:", value=errors, inline=False)
            await ctx.send(embed=embed)
            return errors

        func = env["func"]
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception:
            # In case there's an error, add it to the embed, send and stop.
            value = stdout.getvalue()
            errors = f"```py\n{value}{traceback.format_exc()}\n```"
            embed.add_field(name="Errors:", value=errors, inline=False)
            await ctx.send(embed=embed)

        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction("\u2705")
            except Exception:
                pass

            if ret is None:
                if value:
                    # Output.
                    output = f"```py\n{value}\n```"
                    embed.add_field(name="Output:", value=output, inline=False)
                    await ctx.send(embed=embed)
            else:
                # Maybe the case where there's no output?
                self._last_result = ret
                output = f"```py\n{value}{ret}\n```"
                embed.add_field(name="Output:", value=output, inline=False)
                await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    @commands.before_invoke(record_usage)
    @commands.command(name="rules")
    async def rules(self, ctx: Context):
        """Generates the #rules channel embeds."""
        embed = embeds.make_embed(color=0x7d98e9)
        embed.set_image(url="https://cdn.discordapp.com/attachments/835088653981581312/902441305836244992/AnimePiracy-Aqua-v2-Revision5.7.png")
        await ctx.send(embed=embed)

        embed = embeds.make_embed(
            description=(
                "**1. Do not share copyright infringing files or links**\n"
                "Sharing illegal streaming sites, downloads, torrents, magnet links, trackers, NZBs, or any other form of warez puts our community at risk of being shut down. We are a discussion community, not a file-sharing hub.\n\n"

                "**2. Treat others the way you want to be treated**\n"
                "Attacking, belittling, or instigating drama with others will result in your removal from the community. Any form of prejudice, including but not limited to race, religion, gender, sexual identity, or ethnic background, will not be tolerated.\n\n"

                "**3. Do not disrupt chat**\n"
                "Avoid spamming, derailing conversations, trolling, posting in the incorrect channel, or disregarding channel rules. We expect you to make a basic attempt to fit in and not cause problems.\n\n"

                "**4. Do not abuse pings**\n"
                "Attempting to mass ping, spam ping, ghost ping, or harassing users with pings is not allowed. VIPs should not be pinged for help with their service. <@&763031634379276308> should only be pinged when the situation calls for their immediate attention.\n\n"

                "**5. Do not attempt to evade mod actions**\n"
                "Abusing the rules, such as our automod system, will not be tolerated. Subsequently, trying to find loopholes in the rules to evade mod action is not allowed and will result in a permanent ban.\n\n"

                "**6. Do not post unmarked spoilers**\n"
                "Be considerate and [use spoiler tags](https://support.discord.com/hc/en-us/articles/360022320632-Spoiler-Tags-) when discussing plot elements. Specify which title, series, or episode your spoiler is referencing outside the spoiler tag so that people don't blindly click a spoiler.\n\n"

                "**7. All conversation must be in English**\n"
                "No language other than English is permitted. We appreciate other languages and cultures, but we can only moderate the content we understand.\n\n"

                "**8. Do not post self-promotional content**\n"
                "We are not a billboard for you to advertise your Discord server, social media channels, referral links, personal projects, or services. Unsolicited spam via DMs will result in an immediate ban.\n\n"

                "**9. One account per person per lifetime**\n"
                "Anyone found sharing or using alternate accounts will be banned. Contact staff if you feel you deserve an exception.\n\n"

                "**10. Do not give away, trade, or misuse invites**\n"
                "Invites are intended for personal acquaintances. Publicly offering, requesting, or giving away invites to private trackers, DDL communities, or Usenet indexers is not allowed.\n\n"

                "**11. Do not post NSFL content**\n"
                "NSFL content is described as \"content which is so nauseating or disturbing that it might be emotionally scarring to view.\" Content marked NSFL may contain fetish pornography, gore, or lethal violence.\n\n"

                "**12. Egregious profiles are not allowed**\n"
                "Users with excessively offensive usernames, nicknames, avatars, server profiles, or statuses may be asked to change the offending content or may be preemptively banned in more severe cases."
                ),
            color=0x7d98e9
        )

        await ctx.send(embed=embed)
        await ctx.message.delete()

    @commands.is_owner()
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    @commands.before_invoke(record_usage)
    @commands.command(name="createticketembed")
    async def create_ticket_embed(self, ctx: Context):
        embed = embeds.make_embed(
            title="🎫 Create a new modmail ticket",
            description="Click the react below to create a new modmail ticket.",
            color="default",
        )
        embed.add_field(
            name="Warning:",
            value="Serious inquiries only. Abuse may result in warning or ban.",
        )
        spawned = await ctx.send(embed=embed)
        await spawned.add_reaction("🎫")
        await ctx.message.delete()

    @commands.is_owner()
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    @commands.before_invoke(record_usage)
    @commands.command(name="createcolorrolesembed", aliases=["ccre"])
    async def create_color_roles_embed(self, ctx: Context):
        embed = discord.Embed(
            description=(
                "You can react to one of the squares below to be assigned a colored user role. "
                f"If you are interested in a different color, you can become a <@&{config['roles']['nitro_booster']}> "
                "to receive a custom colored role."
            )
        )

        msg = await ctx.send(embed=embed)

        # API call to fetch all the emojis to cache, so that they work in future calls
        emotes_guild = await ctx.bot.fetch_guild(config["emoji_guild_ids"][0])
        await emotes_guild.fetch_emojis()

        await msg.add_reaction(":redsquare:805032092907601952")
        await msg.add_reaction(":orangesquare:805032107952308235")
        await msg.add_reaction(":yellowsquare:805032120971165709")
        await msg.add_reaction(":greensquare:805032132325801994")
        await msg.add_reaction(":bluesquare:805032145030348840")
        await msg.add_reaction(":pinksquare:805032162197635114")
        await msg.add_reaction(":purplesquare:805032172074696744")
        await ctx.message.delete()

    @commands.is_owner()
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    @commands.before_invoke(record_usage)
    @commands.command(name="createassignablerolesembed", aliases=["care"])
    async def create_assignable_roles_embed(self, ctx: Context):
        role_assignment_text = """
        You can react to one of the emotes below to assign yourself an event role.

        🎁  <@&832528733763928094> - Receive giveaway pings.
        📢  <@&827611682917711952> - Receive server announcement pings.
        📽  <@&831999443220955136> - Receive group watch event pings.
        <:kakeraW:830594599001129000>  <@&832512304334766110> - Receive Mudae event and season pings.
        🧩  <@&832512320306675722> - Receive Rin event pings.
        """
        embed = discord.Embed(description=role_assignment_text)
        msg = await ctx.send(embed=embed)

        # API call to fetch all the emojis to cache, so that they work in future calls
        emotes_guild = await ctx.bot.fetch_guild(config["emoji_guild_ids"][0])
        await emotes_guild.fetch_emojis()

        await msg.add_reaction("🎁")
        await msg.add_reaction("📢")
        await msg.add_reaction("📽")
        await msg.add_reaction(":kakeraW:830594599001129000")
        await msg.add_reaction("🧩")
        await ctx.message.delete()

    @commands.is_owner()
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    @commands.before_invoke(record_usage)
    @commands.command(name="createtestroles")
    async def testroles(self, ctx: Context):
        # Embed for default user color selections
        embed = discord.Embed(description="You can select an option below to be assigned a colored user role.")
        select = create_select(
            options=[  # the options in your dropdown
                create_select_option("Red", value="804644608293208065", emoji=discord.utils.get(self.bot.emojis, name="redsquare")),
                create_select_option("Orange", value="804889570633187358", emoji=discord.utils.get(self.bot.emojis, name="orangesquare")),
                create_select_option("Yellow", value="804889964810469456", emoji=discord.utils.get(self.bot.emojis, name="yellowsquare")),
                create_select_option("Green", value="804889968290824244", emoji=discord.utils.get(self.bot.emojis, name="greensquare")),
                create_select_option("Blue", value="804889972091912202", emoji=discord.utils.get(self.bot.emojis, name="bluesquare")),
                create_select_option("Purple", value="804889978672513034", emoji=discord.utils.get(self.bot.emojis, name="purplesquare")),
                create_select_option("Pink", value="804889975103422477", emoji=discord.utils.get(self.bot.emojis, name="pinksquare")),
                create_select_option("Remove", value="remove", emoji="🚫"),
            ],
            placeholder="Choose your role color",
            min_values=1,
            max_values=1,
        )
        await ctx.send(embed=embed, components=[create_actionrow(select)])

        # Embed for high level users selections
        embed = discord.Embed(description=f"Users who are <@&{config.roles['role_level_10']}> or higher can use the alternative color palette below.")
        select = create_select(
            options=[  # the options in your dropdown
                create_select_option("Gerbera Red", value="843860925298901073", emoji=discord.utils.get(self.bot.emojis, name="betterred")),
                create_select_option("Mikan Orange", value="843862370178695199", emoji=discord.utils.get(self.bot.emojis, name="betterorange")),
                create_select_option("Kiwi Green", value="843862741176418305", emoji=discord.utils.get(self.bot.emojis, name="bettergreen")),
                create_select_option("Hyacinth Blue", value="843863397153374229", emoji=discord.utils.get(self.bot.emojis, name="betterblue")),
                create_select_option("Violet Purple", value="843860376366219325", emoji=discord.utils.get(self.bot.emojis, name="betterpurple")),
                create_select_option("Snowy White", value="859498075483406337", emoji=discord.utils.get(self.bot.emojis, name="betterwhite")),
                create_select_option("Remove", value="remove", emoji="🚫"),
            ],
            placeholder="Choose your role color (level 10+)",
            min_values=1,
            max_values=1,
        )
        await ctx.send(embed=embed, components=[create_actionrow(select)])

        # Embed for telling the users about the benefits of boosting the server.
        embed = discord.Embed(description=f"Users who boost the server are entitled to a custom role with a color of their choice per boost, consider becoming a <@&{config.role_server_booster}>")
        await ctx.send(embed=embed)

        # Embed for general role pickups.
        embed = discord.Embed(description="You can select an option below to be assigned an event role.")
        select = create_select(
            options=[  # the options in your dropdown
                create_select_option("Giveaway Events", value="843860925298901073", emoji="🎁"),
                create_select_option("Server Announcements", value="843862370178695199", emoji="📢"),
                create_select_option("Watch Party", value="843862741176418305", emoji="📽️"),
                create_select_option("Mudae Player", value="843863397153374229", emoji=discord.utils.get(self.bot.emojis, name="kakeraW")),
                create_select_option("Rin Player", value="843860376366219325", emoji="🧩"),
                create_select_option("Remove All", value="remove", emoji="🚫"),
            ],
            placeholder="Choose your event role (level 10+)",
            min_values=1,
            max_values=5,
        )
        await ctx.send(embed=embed, components=[create_actionrow(select)])

    @commands.Cog.listener()
    async def on_component(self, ctx: ComponentContext):
        async def wipe_colors(ctx: ComponentContext):
            colors = list(config.roles_colors.values()) + list(config.roles_colors_lvl10.values())
            # Remove any existing color roles before adding the desired color role.
            for role in ctx.author.roles:
                if role.id in colors:
                    role = discord.utils.get(ctx.guild.roles, id=role.id)
                    await ctx.author.remove_roles(role)

        # Do not process if the component selector is not in the config.
        if ctx.origin_message_id not in [config.select_colors, config.select_colors_lvl10, config.select_events]:
            embed = embeds.make_embed(description="🚫 Attempted to use an invalid selector.", color="soft_red")
            await ctx.send(embed=embed, hidden=True)
            return

        # A user interacted with the color selector.
        if ctx.origin_message_id == config.select_colors:
            # Remove any existing color roles before adding the desired color role.
            await wipe_colors(ctx=ctx)

            # If the user just wanted to remove the role, we can just skip adding the new role.
            if ctx.selected_options[0] == "remove":
                embed = embeds.make_embed(description="✅ Successfully removed role.", color="soft_green")
                await ctx.send(embed=embed, hidden=True)
                return

            # Add the desired color role.
            role = discord.utils.get(ctx.guild.roles, id=int(ctx.selected_options[0]))
            await ctx.author.add_roles(role)

            # Send a successful embed when the role is added
            embed = embeds.make_embed(description="✅ Successfully added role.", color="soft_green")
            await ctx.send(embed=embed, hidden=True)

        # A user interacted with the level 10 color selector.
        if ctx.origin_message_id == config.select_colors_lvl10:
            # Grab the IDs for the last 10 roles in the leveling system.
            roles = list(config.roles.values())[9:20]

            # If the user does not have any level 10+ roles, exit the function.
            if not any(role.id in roles for role in ctx.author.roles):
                embed = embeds.make_embed(description="🚫 You must be level 10+ to use this color palette.", color="soft_red")
                await ctx.send(embed=embed, hidden=True)
                return False

            # Remove any existing color roles before adding the desired color role.
            await wipe_colors(ctx=ctx)

            # If the user just wanted to remove the role, we can just skip adding the new role.
            if ctx.selected_options[0] == "remove":
                embed = embeds.make_embed(description="✅ Successfully removed role.", color="soft_green")
                await ctx.send(embed=embed, hidden=True)
                return

            # Add the desired color role.
            role = discord.utils.get(ctx.guild.roles, id=int(ctx.selected_options[0]))
            await ctx.author.add_roles(role)

            # Send a successful embed when the role is added
            embed = embeds.make_embed(description="✅ Successfully added role.", color="soft_green")
            await ctx.send(embed=embed, hidden=True)

        # A user interacted with the event selector.
        if ctx.origin_message_id == config.select_events:
            if "remove" in ctx.selected_options:
                roles = list(config.roles_events.values())
                await ctx.author.remove_roles(roles)

                embed = embeds.make_embed(description="✅ Successfully removed all roles.", color="soft_green")
                await ctx.send(embed=embed, hidden=True)
                return

            for role in ctx.selected_options:
                await ctx.author.add_roles(ctx.selected_options)

                embed = embeds.make_embed(description="✅ Successfully added selected roles.", color="soft_green")
                await ctx.send(embed=embed, hidden=True)


def setup(bot: Bot) -> None:
    """Load the AdministrationCog cog."""
    bot.add_cog(AdministrationCog(bot))
    log.info("Commands loaded: administration")
