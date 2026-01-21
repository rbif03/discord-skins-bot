import asyncio
from urllib.parse import unquote

import discord
from discord.ext import commands, tasks


import config
from services.dynamodb import (
    add_guild_to_db,
    update_guild_channel,
    add_to_tracked_skins,
    SkinAlreadyTrackedException,
    TrackedSkinsLimitExceededError,
)
from services.ssm import get_parameter
from utils.render_messages import (
    render_formatting_help_msg,
    render_no_active_listings_msg,
)
from utils.validate_skin import get_SkinValidator_obj


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

PARAMETER_NAME = config.DISCORD_TOKEN_SSM_PATH
DISCORD_TOKEN = get_parameter(PARAMETER_NAME)
COMMAND_PREFIX = "->"

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)


@bot.event
async def on_ready() -> None:
    print(f"Logged in as {bot.user.name} - {bot.user.id}")
    print("------")
    return


@bot.event
async def on_guild_join(guild: discord.Guild) -> None:
    await asyncio.to_thread(add_guild_to_db, guild.id)
    print(f"Bot joined guild {guild.id}")
    return


@bot.command()
async def set_skinsbot_channel(ctx: commands.Context) -> None:
    guild_obj = ctx.guild
    channel_obj = ctx.channel
    try:
        await asyncio.to_thread(update_guild_channel, guild_obj.id, channel_obj.id)
        await channel_obj.send(
            f":white_check_mark: The channel '{channel_obj.name}' will now receive skin prices updates!"
        )
    except Exception as e:
        await channel_obj.send(f":cross_mark: Failed to change channel. {e}")

    return


@bot.command()
async def add_skin(ctx: commands.Context) -> None:
    guild_obj = ctx.guild
    channel_obj = ctx.channel
    head = f"{ctx.prefix}{ctx.invoked_with}"
    message = ctx.message.content[len(head) :].strip()
    SkinValidator_obj = await asyncio.to_thread(
        get_SkinValidator_obj, message, COMMAND_PREFIX
    )
    if SkinValidator_obj.validation_status == "error":
        await channel_obj.send(SkinValidator_obj.message)
        return

    # At this point, we know the skin name is valid
    hash_name = SkinValidator_obj.hash_name
    try:
        await asyncio.to_thread(add_to_tracked_skins, guild_obj.id, hash_name)
    except SkinAlreadyTrackedException:
        await channel_obj.send(":cross_mark: That skin is already being tracked!")
        return
    except TrackedSkinsLimitExceededError:
        await channel_obj.send(
            ":cross_mark: Tracking limit reached for this server. Remove a tracked skin before adding another."
        )
        return
    except Exception as e:
        await channel_obj.send(f":cross_mark: Failed to add skin to the database. {e}")
        return

    unquoted_hash_name = unquote(hash_name)
    await channel_obj.send(
        f":white_check_mark: Successfully added `{unquoted_hash_name}` to tracked skins!"
    )

    return


@bot.command()
async def formatting_help(ctx: commands.Context) -> None:
    channel_obj = ctx.channel
    await channel_obj.send(render_formatting_help_msg(COMMAND_PREFIX))
    return


bot.run(DISCORD_TOKEN)
