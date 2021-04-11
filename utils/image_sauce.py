import asyncio
from discord.ext.commands.context import Context
from saucenao_api import SauceNao, VideoSauce, BookSauce
import discord
import discord.ext.commands

import config
from utils import embeds


sauce = SauceNao(config.saucenao_api_key)


def _get_page(result, page: int, ctx: Context) -> discord.Embed:
    # Fetches page x from result list and prepares a nice embed.
    data = result[page]
    embed = embeds.make_embed("Sauce Found!", f"Page {page+1} of {len(result)}", ctx, 'gold')
    embed.set_thumbnail(url=data.thumbnail)
    embed.add_field(name="Title", value=data.title, inline=True)
    embed.add_field(name="Author", value=data.author, inline=True)
    embed.add_field(name="Match", value=f"{data.similarity}%", inline=False)
    urls = ""
    for x in data.urls:
        urls = f"{urls}\n{x}"
    
    if len(urls) == 0:
        urls = "None found."
    embed.add_field(name="URLs", value=urls, inline=True)

    if isinstance(result, VideoSauce):
        embed.add_field(name="Timestamp", value=data.est_time, inline=False)

    return embed


async def paginate_image_sauce(ctx: Context, url):
    result = None
    async with ctx.typing():
        result = sauce.from_url(url)

    if (not bool(result)):
        # nothing found, so display an error
        await embeds.error_message("No results found.")
        return
    
    FIRST_EMOJI = "\u23EE"   # [:track_previous:]
    LEFT_EMOJI = "\u2B05"    # [:arrow_left:]
    RIGHT_EMOJI = "\u27A1"   # [:arrow_right:]
    LAST_EMOJI = "\u23ED"    # [:track_next:]
    DELETE_EMOJI = "⛔"  # [:trashcan:]
    SAVE_EMOJI = "💾"  # [:floppy_disk:]

    bot = ctx.bot
    timeout = 30

    PAGINATION_EMOJI = (FIRST_EMOJI, LEFT_EMOJI, RIGHT_EMOJI,
                        LAST_EMOJI, DELETE_EMOJI, SAVE_EMOJI)

    page_no = 0
    msg = await ctx.send(embed=_get_page(result, page_no, ctx))

    for x in PAGINATION_EMOJI:
        await msg.add_reaction(x)

    def check(reaction: discord.Reaction, user: discord.Member) -> bool:
        if reaction.emoji in PAGINATION_EMOJI and user == ctx.author:
            return True

        return False

    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=timeout, check=check)

        except asyncio.TimeoutError:
            await msg.delete()
            break

        if str(reaction.emoji) == DELETE_EMOJI:
            await msg.delete()
            break

        if str(reaction.emoji) == SAVE_EMOJI:
            await msg.clear_reactions()
            break

        if reaction.emoji == FIRST_EMOJI:
            await msg.remove_reaction(reaction.emoji, user)
            page_no = 0

        if reaction.emoji == LAST_EMOJI:
            await msg.remove_reaction(reaction.emoji, user)
            page_no = len(result) - 1

        if reaction.emoji == LEFT_EMOJI:
            await msg.remove_reaction(reaction.emoji, user)

            if page_no <= 0:
                page_no = len(result) - 1

            else:
                page_no -= 1

        if reaction.emoji == RIGHT_EMOJI:
            await msg.remove_reaction(reaction.emoji, user)

            if page_no >= len(result) - 1:
                page_no = 0

            else:
                page_no += 1

        embed = _get_page(result, page_no, ctx)

        if embed is not None:
            await msg.edit(embed=embed)



    

    


