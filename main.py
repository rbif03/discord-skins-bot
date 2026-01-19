import asyncio
from urllib.parse import unquote

import discord
from discord.ext import commands, tasks

import config
from services.dynamodb import add_guild_to_db, update_guild_channel
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
async def on_ready():
    print(f"Logged in as {bot.user.name} - {bot.user.id}")
    print("------")
    return


@bot.event
async def on_guild_join(guild: discord.Guild):
    await asyncio.to_thread(add_guild_to_db, guild.id)
    print(f"Bot joined guild {guild.id}")
    return


@bot.command()
async def set_skinsbot_channel(ctx: commands.Context):
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
async def add_skin(ctx: commands.Context):
    channel_obj = ctx.channel
    head = f"{ctx.prefix}{ctx.invoked_with}"
    message = ctx.message.content[len(head) :].strip()
    skin_is_valid_dict = await asyncio.to_thread(validate_skin_from_message, message)
    if skin_is_valid_dict.get("is_valid"):
        unquoted_hash_name = unquote(skin_is_valid_dict.get("hash_name"))
        await channel_obj.send(
            f":white_check_mark: Successfully added `{unquoted_hash_name}` to tracked skins!"
        )
    else:
        await channel_obj.send(
            """:cross_mark: No active listings found for that skin.

            1) Check the spelling, or try adding wear (e.g. Field-Tested).
            2) If it's extremely rare, it may not be trackable.

            Examples:
            - `AWP | Safari Mesh (Field-Tested)`
            - `https://steamcommunity.com/market/listings/730/StatTrak%E2%84%A2%20AUG%20%7C%20Triqua%20%28Well-Worn%29`

            Need help? Type `->format`."""
        )


bot.run(DISCORD_TOKEN)
