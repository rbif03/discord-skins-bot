import asyncio
import logging

import boto3
from boto3.dynamodb.conditions import Key

from models.result import Result

logger = logging.getLogger(__name__)
dynamodb_client = boto3.resource("dynamodb")
guild_info_table = dynamodb_client.Table("skinsbot.guild_info")


def add_guild_or_raise(guild_id: int) -> None:
    # Checks if guild is already in DB, if not, adds it
    response: dict = guild_info_table.query(
        KeyConditionExpression=Key("guild_id").eq(guild_id)
    )

    if not response.get("Items"):
        data = {"guild_id": guild_id, "max_tracked_skins": 10}
        guild_info_table.put_item(Item=data)


async def add_guild(guild_id: int) -> Result:
    try:
        await asyncio.to_thread(add_guild_or_raise, guild_id)
        return Result(success=True)

    except Exception as e:
        text = "Failed to add guild to database."
        exception_text = f"{type(e).__name__}: {e}"
        logger.error(f"{text} guild_id={guild_id} {exception_text}")
        return Result(success=False, text=text)


def update_channel_or_raise(guild_id: int, channel_id: int) -> None:
    add_guild_or_raise(guild_id)  # if the guild isn't in DB for some reason, adds it

    guild_info_table.update_item(
        Key={"guild_id": guild_id},
        UpdateExpression="SET channel_id = :channel_id",
        ExpressionAttributeValues={":channel_id": channel_id},
    )


async def update_channel(guild_id: int, channel_id: int) -> Result:
    try:
        await asyncio.to_thread(update_channel_or_raise, guild_id, channel_id)
        return Result(
            success=True,
            text=":white_check_mark: The channel '{channel_name}' will now receive skin prices updates!",
        )

    except Exception as e:
        text = "Failed to update to channel."
        exception_text = f"{type(e).__name__}: {e}"
        logger.error(
            f"{text} guild_id={guild_id} channel_id={channel_id} {exception_text}"
        )
        return Result(
            success=False,
            text=text,
        )


def get_max_tracked_skins_or_raise(guild_id: int) -> int:
    response: dict = guild_info_table.query(
        KeyConditionExpression=Key("guild_id").eq(guild_id)
    )
    if response.get("Items"):
        max_tracked_skins = response.get("Items")[0].get("max_tracked_skins")
        return max_tracked_skins

    return 0  # This is for a guild_id that is not in the db
