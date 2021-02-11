import html
import asyncio
import requests
import discord
import discord.ext.commands

from contextlib import suppress
from discord.ext.commands import Context

from utils import embeds

async def find_anime(search_term):
    URL = 'https://graphql.anilist.co'
    query = '''
    query($term: String) {
        Page(page:1, perPage:10) {
            media(search:$term, type:ANIME, sort:POPULARITY_DESC) {
            id
            idMal
            title {
                userPreferred
                romaji
                english
                native
            }
            coverImage {
                medium
                extraLarge
            }
            isAdult
            description
            episodes
            duration
            siteUrl
            tags {
                name
            }
            nextAiringEpisode {
                episode
                airingAt
                timeUntilAiring
            }
            }
        }
    }
    '''
    variables = {
        'term': search_term
    }
    response = requests.post(
        URL, json={'query': query, 'variables': variables})
    return response.json()["data"]["Page"]

def get_page(search_result_list, page_no, ctx: Context) -> discord.Embed:
    if page_no >= len(search_result_list) or page_no < 0:
        return None

    anime_data = search_result_list[page_no]
    
    embed = embeds.make_embed(title="Anime Search", context=ctx, color='gold')

    try:
        embed = embeds.make_embed(title="Anime Search", context=ctx, color='gold')
        embed.set_thumbnail(url=anime_data['coverImage']['extraLarge'])
        
        anime_name = anime_data['title']['english']+"("+anime_data['title']['romaji']+")"
        embed.add_field(name="Anime Name", value=anime_name, inline=False)
        
        description = html.unescape(anime_data['description'])
        if len(description) > 512:
            description = description[0:512] + "..."
        
        embed.add_field(name="Description", value=description, inline=False)

        embed.add_field(name="URL", value=anime_data['siteUrl'])

        if(anime_data['nextAiringEpisode']):
            embed.add_field(name="Next Airing Episode", value=anime_data['nextAiringEpisode']['episode'], inline=True)
            embed.add_field(name="Next Episode In", value=anime_data['nextAiringEpisode']['timeUntilAiring'])

    except:
        return None

    return embed

async def anime_paginator(search_results ,ctx: Context):
    FIRST_EMOJI = "\u23EE"   # [:track_previous:]
    LEFT_EMOJI = "\u2B05"    # [:arrow_left:]
    RIGHT_EMOJI = "\u27A1"   # [:arrow_right:]
    LAST_EMOJI = "\u23ED"    # [:track_next:]
    DELETE_EMOJI = "⛔"  # [:trashcan:]

    bot = ctx.bot
    timeout = 30

    PAGINATION_EMOJI = (FIRST_EMOJI, LEFT_EMOJI, RIGHT_EMOJI, LAST_EMOJI, DELETE_EMOJI)

    page_no = 0
    msg = await ctx.send(embed=get_page(search_results, page_no, ctx))

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
            break


        if str(reaction.emoji) == DELETE_EMOJI:
            await msg.delete()
            break

        if reaction.emoji == FIRST_EMOJI:
            await msg.remove_reaction(reaction.emoji, user)
            page_no = 0
        
        if reaction.emoji == LAST_EMOJI:
            await msg.remove_reaction(reaction.emoji, user)
            page_no = len(search_results) - 1

        if reaction.emoji == LEFT_EMOJI:
            await msg.remove_reaction(reaction.emoji, user)

            if page_no <= 0:
                continue

            page_no -= 1

        if reaction.emoji == RIGHT_EMOJI:
            await msg.remove_reaction(reaction.emoji, user)

            if page_no >= len(search_results) - 1:
                continue

            page_no+=1
        
        embed = get_page(search_results, page_no, ctx)
        
        if embed is not None:
            await msg.edit(embed=embed)





    

            
