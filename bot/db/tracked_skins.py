import asyncio
import logging
from urllib.parse import unquote

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from db.exceptions import (
    TrackedSkinsLimitExceededError,
    SkinAlreadyTrackedError,
    SkinNotTrackedError,
)
from db.guild_info import get_max_tracked_skins_or_raise
from models.result import Result

logger = logging.getLogger(__name__)
dynamodb_client = boto3.resource("dynamodb")
tracked_skins_table = dynamodb_client.Table("skinsbot.tracked_skins")


def get_tracked_hash_names_or_raise(guild_id: int) -> list[str]:
    response: dict = tracked_skins_table.query(
        KeyConditionExpression=Key("guild_id").eq(guild_id)
    )
    guild_tracked_hash_names = [
        d.get("hash_name") for d in response.get("Items") if d.get("hash_name")
    ]
    return guild_tracked_hash_names


async def get_tracked_hash_names(guild_id: int) -> Result:
    try:
        tracked_hash_names = await asyncio.to_thread(
            get_tracked_hash_names_or_raise, guild_id
        )
        unquoted_hash_names = [f"`{unquote(skin)}`" for skin in tracked_hash_names]

        if len(tracked_hash_names) > 0:
            text = f"Tracked skins:\n* " + "\n* ".join(unquoted_hash_names)
        else:
            text = f":cross_mark: This server has no tracked skins. Use `->add_skin <skin name>`"
        return Result(
            success=True, text=text, data={"tracked_hash_names": tracked_hash_names}
        )

    except Exception as e:
        text = "Failed to get tracked hash names."
        exception_text = f"{type(e).__name__}: {e}"
        logger.error(f"{text} guild_id={guild_id} {exception_text}")
        return Result(success=False, text=text)


def track_hash_name_or_raise(guild_id: int, hash_name: str) -> None:
    guild_tracked_hash_names = get_tracked_hash_names_or_raise(guild_id)
    if hash_name in guild_tracked_hash_names:
        raise SkinAlreadyTrackedError(
            f":cross_mark: Skin {unquote(hash_name)} is already being tracked!"
        )

    max_tracked_skins = get_max_tracked_skins_or_raise(guild_id)
    if len(guild_tracked_hash_names) >= max_tracked_skins:
        raise TrackedSkinsLimitExceededError(
            f":cross_mark: Tracking limit ({max_tracked_skins}) reached for this server. Remove a tracked skin before adding another."
        )

    tracked_skins_table.put_item(Item={"guild_id": guild_id, "hash_name": hash_name})


async def track_hash_name(guild_id: int, hash_name: str) -> Result:
    try:
        await asyncio.to_thread(track_hash_name_or_raise, guild_id, hash_name)
        return Result(
            success=True,
            text=f":white_check_mark: Successfully added `{unquote(hash_name)}` to tracked skins!",
        )

    except SkinAlreadyTrackedError as e:
        return Result(success=False, text=str(e))

    except TrackedSkinsLimitExceededError as e:
        return Result(success=False, text=str(e))

    except Exception as e:
        text = f"Failed to track hash name {hash_name}."
        exception_text = f"{type(e).__name__}: {e}"
        logger.error(f"{text} guild_id={guild_id} {exception_text}")
        return Result(success=False, text=text)


def untrack_hash_name_or_raise(guild_id: int, hash_name: str) -> None:
    tracked_skins_table.delete_item(
        Key={"guild_id": guild_id, "hash_name": hash_name},
        ConditionExpression="attribute_exists(guild_id) AND attribute_exists(hash_name)",
    )


async def untrack_hash_name(guild_id: int, hash_name: str) -> Result:
    try:
        await asyncio.to_thread(untrack_hash_name_or_raise, guild_id, hash_name)
        text = f":white_check_mark: `{unquote(hash_name)}` removed from tracked skins!"
        return Result(success=True, text=text)

    except ClientError as e:
        code = e.response.get("Error", {}).get("Code")
        if code == "ConditionalCheckFailedException":
            msg = f"Unable to untrack skin `{unquote(hash_name)}`, since it is not among currently tracked skins."
            return Result(success=False, text=msg)

        else:
            text = f"Failed to untrack hash name {hash_name}."
            exception_text = f"{type(e).__name__}: {e}"
            logger.error(f"{text} guild_id={guild_id} {exception_text}")
            return Result(success=False, text=text)

    except Exception as e:
        text = f"Failed to untrack hash name {hash_name}."
        exception_text = f"{type(e).__name__}: {e}"
        logger.error(f"{text} guild_id={guild_id} {exception_text}")
        return Result(success=False, text=text)
