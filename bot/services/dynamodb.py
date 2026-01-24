import time
from urllib.parse import unquote

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from models.validation_response import SkinValidationResponse

dynamodb_client = boto3.resource("dynamodb")
guild_info_table = dynamodb_client.Table("skinsbot.guild_info")
tracked_skins_table = dynamodb_client.Table("skinsbot.tracked_skins")
skin_prices_table = dynamodb_client.Table("skinsbot.skin_prices")


class SkinNotTrackedException(Exception):
    pass


class SkinAlreadyTrackedException(Exception):
    user_message = ":cross_mark: That skin is already being tracked!"


class TrackedSkinsLimitExceededError(Exception):
    user_message = ":cross_mark: Tracking limit reached for this server. Remove a tracked skin before adding another."


class CurrentPriceNotFound(Exception):
    pass


def add_guild_to_db(guild_id: int) -> None:
    # Checks if guild is already in DB, if not, adds it
    response: dict = guild_info_table.query(
        KeyConditionExpression=Key("guild_id").eq(guild_id)
    )

    if not response.get("Items"):
        guild_info_table.put_item(Item={"guild_id": guild_id, "max_tracked_skins": 10})


def update_guild_channel(guild_id: int, channel_id: int) -> None:
    add_guild_to_db(guild_id)  # if the guild isn't in DB for some reason, adds it

    guild_info_table.update_item(
        Key={"guild_id": guild_id},
        UpdateExpression="SET channel_id = :channel_id",
        ExpressionAttributeValues={":channel_id": channel_id},
    )


def get_guild_channel(guild_id: int) -> None:
    try:
        response = guild_info_table.query(
            KeyConditionExpression=Key("guild_id").eq(guild_id)
        )
        if len(response.get("Items", [])) == 0:
            return None

        channel_id = response.get("Items")[0]["channel_id"]
        return channel_id
    except Exception:
        return None


def get_guild_tracked_hash_names(guild_id: int) -> list[str]:
    response: dict = tracked_skins_table.query(
        KeyConditionExpression=Key("guild_id").eq(guild_id)
    )
    guild_tracked_hash_names = [
        d.get("hash_name") for d in response.get("Items") if d.get("hash_name")
    ]
    return guild_tracked_hash_names


def get_guild_max_tracked_skins(guild_id: int) -> int:
    response: dict = guild_info_table.query(
        KeyConditionExpression=Key("guild_id").eq(guild_id)
    )
    if response.get("Items"):
        max_tracked_skins = response.get("Items")[0].get("max_tracked_skins")
        return max_tracked_skins

    return 0  # This is for a guild_id that is not in the db


def add_to_tracked_skins(guild_id: int, hash_name: str) -> None:
    guild_tracked_hash_names = get_guild_tracked_hash_names(guild_id)
    if hash_name in guild_tracked_hash_names:
        raise SkinAlreadyTrackedException

    max_tracked_skins = get_guild_max_tracked_skins(guild_id)
    if len(guild_tracked_hash_names) >= max_tracked_skins:
        raise TrackedSkinsLimitExceededError

    tracked_skins_table.put_item(Item={"guild_id": guild_id, "hash_name": hash_name})
    return


def try_except_add_to_tracked_skins(
    guild_id: int, hash_name: str
) -> SkinValidationResponse:
    try:
        add_to_tracked_skins(guild_id, hash_name)
        return SkinValidationResponse(
            hash_name=hash_name,
            status="success",
        )
    except SkinAlreadyTrackedException as e:
        return SkinValidationResponse(
            hash_name=hash_name, status="error", text=e.user_message
        )
    except TrackedSkinsLimitExceededError as e:
        return SkinValidationResponse(
            hash_name=hash_name, status="error", text=e.user_message
        )
    except Exception as e:
        return SkinValidationResponse(
            hash_name=hash_name, status="error", text=f"DynamoDB (database) error: {e}"
        )


def get_tracked_hash_names(guild_id: int) -> list[str]:
    response: dict = tracked_skins_table.query(
        KeyConditionExpression=Key("guild_id").eq(guild_id)
    )
    tracked_hash_names = [
        d.get("hash_name") for d in response.get("Items", []) if d.get("hash_name")
    ]
    return sorted(tracked_hash_names)


def delete_tracked_skin(guild_id: int, hash_name: str) -> list[str]:
    try:
        tracked_skins_table.delete_item(
            Key={"guild_id": guild_id, "hash_name": hash_name},
            ConditionExpression="attribute_exists(guild_id) AND attribute_exists(hash_name)",
        )
    except ClientError as e:
        code = e.response["Error"].get("Code")
        if code == "ConditionalCheckFailedException":
            raise SkinNotTrackedException
        else:
            raise e


def get_most_recent_price(hash_name: str) -> str:
    unix_now = int(time.time())
    response = skin_prices_table.query(
        KeyConditionExpression=Key("hash_name").eq(hash_name)
        & Key("unix_timestamp").gt(unix_now - 24 * 3600)
    )
    try:
        most_recent_entry = max(
            response.get("Items", []), key=lambda d: d["unix_timestamp"]
        )
        return most_recent_entry["price_usd"]

    except (ValueError, KeyError):
        raise CurrentPriceNotFound(
            f"Couldn't find a price for {unquote(hash_name)} in the last 24h."
        )


if __name__ == "__main__":
    pass
