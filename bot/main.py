from datetime import time, timezone, timedelta
import logging
import sys
from urllib.parse import quote, unquote

import discord
from discord.ext import commands, tasks


import config
import db.guild_info
import db.skins_prices
import db.tracked_skins
from services.ssm import get_parameter
from services.steam_api.validate import get_hash_name, validate_add_skin_argument
from utils.render_messages import render_formatting_help_msg
from utils.bot_utils import get_shutdown_time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    force=True,
)
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

PARAMETER_NAME = config.DISCORD_TOKEN_SSM_PATH
DISCORD_TOKEN = get_parameter(PARAMETER_NAME)
COMMAND_PREFIX = "->"

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)


@bot.event
async def on_guild_join(guild: discord.Guild) -> None:
    result = await db.guild_info.add_guild(guild.id)
    if result.success:
        logger.info(f"Bot joined guild {guild.id}")


@bot.command()
async def set_skinsbot_channel(ctx: commands.Context) -> None:
    guild = ctx.guild
    channel = ctx.channel
    result = await db.guild_info.update_channel(guild.id, channel.id)
    if result.success:
        await channel.send(result.text.format(channel_name=channel.name))
    else:
        await channel.send(result.text)


@bot.command()
async def add_skin(ctx: commands.Context) -> None:
    guild = ctx.guild
    channel = ctx.channel
    head = f"{ctx.prefix}{ctx.invoked_with}"
    command_argument = ctx.message.content[len(head) :].strip()

    argument_validation_result = await validate_add_skin_argument(command_argument)
    if not argument_validation_result.success:
        await channel.send(argument_validation_result.text)
        return

    # At this point, we know the skin name is valid
    hash_name = argument_validation_result.data["hash_name"]
    add_to_db_result = await db.tracked_skins.track_hash_name(guild.id, hash_name)

    await channel.send(add_to_db_result.text)


@bot.command()
async def formatting_help(ctx: commands.Context) -> None:
    channel_obj = ctx.channel
    await channel_obj.send(render_formatting_help_msg(COMMAND_PREFIX))
    return


@bot.command()
async def tracked_skins(ctx: commands.Context) -> None:
    guild = ctx.guild
    channel = ctx.channel

    result = await db.tracked_skins.get_tracked_hash_names(guild.id)
    await channel.send(result.text)


@bot.command()
async def remove_skin(ctx: commands.Context) -> None:
    guild = ctx.guild
    channel = ctx.channel
    head = f"{ctx.prefix}{ctx.invoked_with}"
    command_argument = ctx.message.content[len(head) :].strip()
    hash_name_result = get_hash_name(command_argument)
    if not hash_name_result.success:
        await channel.send(hash_name_result.text)
        return

    hash_name = hash_name_result.data["hash_name"]
    untrack_result = await db.tracked_skins.untrack_hash_name(guild.id, hash_name)
    await channel.send(untrack_result.text)


@tasks.loop(time=time(19, 35))  # UTC
async def send_price_updates():
    guild_list = bot.guilds
    for guild in guild_list:
        get_channel_result = await db.guild_info.get_guild_channel(guild.id)

        # db.guild_info.get_guild_channel already logs the following if statements
        if not get_channel_result.success:
            continue
        channel_id = get_channel_result.data.get("channel_id")
        if channel_id is None:
            continue

        tracked_hash_names_result = await db.tracked_skins.get_tracked_hash_names(
            guild.id
        )
        if not tracked_hash_names_result.success:
            await bot.get_channel(channel_id).send(tracked_hash_names_result.text)
            continue

        message = "Tracked skins prices:\n"
        tracked_hash_names = tracked_hash_names_result.data.get(
            "tracked_hash_names", []
        )
        for hash_name in tracked_hash_names:
            logger.info(f"Getting price for {hash_name}")
            price_result = await db.skins_prices.get_most_recent_price(hash_name)
            if not price_result.success:
                message += f"`{unquote(hash_name)}`: **Price not available**\n"
                continue
            price = price_result.data.get("price_usd")
            price = round(float(price), 2)
            message += f"`{unquote(hash_name)}:` *${f"{price:.2f}"}*\n"

        await bot.get_channel(channel_id).send(message)


@tasks.loop(time=get_shutdown_time())
async def shutdown_bot():
    sys.exit(0)


@bot.event
async def on_ready() -> None:
    if not send_price_updates.is_running():
        send_price_updates.start()
        logger.info("send_price_updates loop started")
    if not shutdown_bot.is_running():
        shutdown_bot.start()
        logger.info(f"bot will be shut down at {get_shutdown_time()}")
    logger.info(f"Logged in as {bot.user.name} - {bot.user.id}")
    return


def handler(event, context):
    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    handler({}, None)
