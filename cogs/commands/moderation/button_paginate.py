import asyncio
import logging
from typing import List


import dataset
from discord_slash.context import ComponentContext
from sqlalchemy.sql.expression import desc

import config
from utils import database

from discord.ext import commands
import discord
from discord.ext.commands.core import group
from utils import embeds
from utils.record import record_usage
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option, create_permission

from discord_slash.model import SlashCommandPermissionType, ButtonStyle
from discord_slash.utils.manage_components import create_button, create_actionrow, wait_for_component
from utils.pagination import LinePaginator


# Enabling logs
log = logging.getLogger(__name__)


class ButtonPaginateCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
    
    async def button_paginator(self, ctx: SlashContext, title: str, items: list, color: str = "default", per_page: int = 5):
        
        FIRST_PAGE_TEXT = "First Page"
        FIRST_PAGE_EMOJI = None
        PREVIOUS_PAGE_TEXT = "Previous"
        PREVIOUS_PAGE_EMOJI = None
        NEXT_PAGE_TEXT = "Next"
        NEXT_PAGE_EMOJI = None
        LAST_PAGE_TEXT = "Last Page"
        LAST_PAGE_EMOJI = None
        SAVE_TEXT = "Save"
        SAVE_EMOJI = None
        DELETE_TEXT = "Delete"
        DELETE_EMOJI = None
        TIMEOUT = 10

        page_buttons = [
            create_button(
                style=ButtonStyle.blue,
                label=FIRST_PAGE_TEXT,
                emoji=FIRST_PAGE_EMOJI,
                custom_id="first_page"
            ),
            create_button(
                style=ButtonStyle.blurple,
                label=PREVIOUS_PAGE_TEXT,
                emoji=PREVIOUS_PAGE_EMOJI,
                custom_id="previous_page"
            ),
            create_button(
                style=ButtonStyle.blurple,
                label=NEXT_PAGE_TEXT,
                emoji=NEXT_PAGE_EMOJI,
                custom_id="next_page"
            ),
            create_button(
                style=ButtonStyle.blue,
                label=LAST_PAGE_TEXT,
                emoji=LAST_PAGE_EMOJI,
                custom_id="last_page"
            ),   
        ]
        control_buttons = [
            create_button(
                style=ButtonStyle.success,
                label=SAVE_TEXT,
                emoji=SAVE_EMOJI,
                custom_id="save_button"
            ),
            create_button(
                style=ButtonStyle.danger,
                label=DELETE_TEXT,
                emoji=DELETE_EMOJI,
                custom_id="delete_button"

            )
        ]
        action_row_pages = create_actionrow(*page_buttons)
        action_row_controls = create_actionrow(*control_buttons)
        page_no = 0
        total_pages = len(items)%per_page + 1

        if len(items) == 0:
            # if the given list is empty
            embed = embeds.make_embed(ctx=ctx, title=title, description="(Nothing to display)", color = color)
            await ctx.send(embed=embed)
            return
        
        # store the per_page number of items temporarily
        page = []
        # store the pages for the paginator
        pages = []

        # Prepare the data for the paginator.
        for item in items:
            page.append(item)
            
            if (page_no + 1) % per_page == 0 and page_no != 0:
                # Appending the current page to the main pages list and resetting the page.
                pages.append(page.copy())
                page = []
            
            page_no+=1
        
        if not (page_no + 1) % per_page == 0 and len(page) != 0:
            # For the situations when some pages were left behind.
            pages.append(page.copy())
        
        def get_page(page_number: int):
            embed = embeds.make_embed(ctx=ctx, title=title, color=color)
            embed_description = f"**Page {page_number+1} of {len(pages)}**\n"
            for item in pages[page_number]:
                embed_description += f"\n{item}"
            embed.description = embed_description
            return embed
        
        page_no = 0

        # Send an initial message and display the first page.
        pagination_message = await ctx.send(embed=get_page(page_no), components=[action_row_pages, action_row_controls])

        def check(check_ctx: ComponentContext):
            if check_ctx.author == ctx.author:
                return True
            return False

        while True:
            try:
                button_ctx = await wait_for_component(self.bot, components=[action_row_controls, action_row_pages], check=check)
                await button_ctx.defer(edit_origin=True)
            except asyncio.TimeoutError:
                await pagination_message.delete()
                return
            
            async def save_embed():
                await pagination_message.edit(components=[])
                exit
            
            async def delete_embed():
                await pagination_message.delete()
                exit

            component_id_mappings = {
                "first_page": 0,
                "last_page": len(pages) - 1,
                "next_page": page_no+1 if page_no < len(pages) else 0,
                "previous_page": page_no-1 if page_no > 0 else len(pages) - 1,
                "save_button" : await save_embed(),
                "delete_button": await delete_embed()
            }
            await button_ctx.edit_origin(embed=get_page(component_id_mappings[button_ctx.component_id]))
            
    
    @commands.before_invoke(record_usage)
    @cog_ext.cog_subcommand(
        name = "test_button",
        description="Testing button embeds.",
        guild_ids=[config.guild_id],
        base_default_permission=False,
        base_permissions={
            config.guild_id: [
                create_permission(config.role_staff, SlashCommandPermissionType.ROLE, True),
                create_permission(config.role_trial_mod, SlashCommandPermissionType.ROLE, True)
            ]
        }
    )
    async def testing(self, ctx: SlashContext):

        await self.button_paginator(ctx=ctx, title="AaAaA", items=["a", "b", "c", "d", "e", "f"])

            
            
def setup(bot) -> None:
    bot.add_cog(ButtonPaginateCog(bot))
    log.info("Cog loaded: ButtonPaginateCog")
