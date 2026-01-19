import asyncio
from urllib.parse import unquote

import discord
from discord.ext import commands, tasks

import config
from services.dynamodb import (
    add_guild_to_db,
    update_guild_channel,
    add_to_tracked_skins,
)
from services.ssm import get_parameter
from utils.validate_skin import validate_skin_from_message


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
    skin_is_valid_dict = await asyncio.to_thread(validate_skin_from_message, message)
    hash_name = skin_is_valid_dict.get("hash_name")
    if skin_is_valid_dict.get("is_valid"):
        await asyncio.to_thread(add_to_tracked_skins, guild_obj.id, hash_name)

        unquoted_hash_name = unquote(hash_name)
        await channel_obj.send(
            f":white_check_mark: Successfully added `{unquoted_hash_name}` to tracked skins!"
        )
    else:
        # TODO: create a separate python file that renders these messages
        await channel_obj.send(
            f":cross_mark: No active listings found for that skin.\n"
            "This usually means:\n"
            f"1) The name is misspelled (see `{COMMAND_PREFIX}formatting_help`).\n"
            "2) The skin is too rare to track reliably."
        )

    return


@bot.command()
async def formatting_help(ctx: commands.Context) -> None:
    channel_obj = ctx.channel
    await channel_obj.send(
        "Skin formatting help\n\n"
        "You can provide a skin in 2 ways:\n\n"
        "1) Skin name (recommended)\n"
        "Use this exact pattern:\n"
        "WEAPON | SKIN NAME (WEAR)\n\n"
        "Examples:\n"
        "`AWP | Safari Mesh (Field-Tested)`\n"
        "`AK-47 | Redline (Minimal Wear)`\n"
        "`Glock-18 | Water Elemental (Factory New)`\n\n"
        "Wear must be one of:\n"
        "`Factory New`, `Minimal Wear`, `Field-Tested`, `Well-Worn`, `Battle-Scarred`\n\n"
        "2) Steam Market link\n"
        "Paste the full listing URL, like:\n"
        "`https://steamcommunity.com/market/listings/730/StatTrak%E2%84%A2%20AUG%20%7C%20Triqua%20%28Well-Worn%29`\n\n"
        "Tips:\n"
        "- Include the wear in parentheses. It matters.\n"
        "- Keep the | between weapon and skin name.\n"
        "- Copy and paste from Steam if possible to avoid typos.\n"
        "- Some skins may be too rare and have no active listings.\n\n"
        f"Example usage:\n"
        f"{COMMAND_PREFIX}add_skin AWP | Safari Mesh (Field-Tested)\n"
        f"{COMMAND_PREFIX}add_skin `https://steamcommunity.com/market/listings/730/...`"
    )
    return


bot.run(DISCORD_TOKEN)
