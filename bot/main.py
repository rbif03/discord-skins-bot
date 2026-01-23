import asyncio
from urllib.parse import quote, unquote

import discord
from discord.ext import commands, tasks


import config
from services.dynamodb import (
    add_guild_to_db,
    update_guild_channel,
    try_except_add_to_tracked_skins,
    get_tracked_hash_names,
    delete_tracked_skin,
    SkinNotTrackedException,
)
from services.ssm import get_parameter
from utils.render_messages import (
    render_formatting_help_msg,
)
from utils.validate_skin import get_SkinValidationResponse


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
    SkinValidationResponse_obj = await asyncio.to_thread(
        get_SkinValidationResponse, message
    )
    if SkinValidationResponse_obj.status == "error":
        await channel_obj.send(SkinValidationResponse_obj.text)
        return

    # At this point, we know the skin name is valid
    hash_name = SkinValidationResponse_obj.hash_name

    add_to_db_validation_obj = await asyncio.to_thread(
        try_except_add_to_tracked_skins, guild_obj.id, hash_name
    )
    if add_to_db_validation_obj.status == "error":
        await channel_obj.send(add_to_db_validation_obj.text)
        return

    # At this point add_to_db_validation_obj.status == "success"
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


@bot.command()
async def tracked_skins(ctx: commands.Context) -> None:
    guild_obj = ctx.guild
    channel_obj = ctx.channel
    try:
        hash_names = await asyncio.to_thread(get_tracked_hash_names, guild_obj.id)
        unquoted_hash_names = [f"`{unquote(skin)}`" for skin in hash_names]
        if len(hash_names) > 0:
            await channel_obj.send(
                f"Tracked skins:\n* " + "\n* ".join(unquoted_hash_names)
            )
        else:
            await channel_obj.send(
                f":cross_mark: This server has no tracked skins. Use `->add_skin <skin name>`"
            )
    except Exception as e:
        await channel_obj.send(f":cross_mark: Failed to fetch tracked skins.\n{e}")


@bot.command()
async def remove_skin(ctx: commands.Context) -> None:
    guild_obj = ctx.guild
    channel_obj = ctx.channel
    head = f"{ctx.prefix}{ctx.invoked_with}"
    message = ctx.message.content[len(head) :].strip()
    hash_name = quote(message)
    try:
        await asyncio.to_thread(delete_tracked_skin, guild_obj.id, hash_name)
        await channel_obj.send(
            f":white_check_mark: `{message}` removed from tracked skins!"
        )
    except SkinNotTrackedException:
        await channel_obj.send(
            f":cross_mark: {message}is not currently tracked. Use->tracked_skins to view tracked skins."
        )
    except Exception as e:
        await channel_obj.send(
            f":cross_mark: Couldn't delete the skin. Try again later. ({e})"
        )

    return


bot.run(DISCORD_TOKEN)
