import boto3

import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource("dynamodb")
guild_info_table = dynamodb.Table("skinsbot.guild_info")


def add_guild_to_db(guild_id: int) -> None:
    # Checks if guild is already in DB, if not, adds it
    response = guild_info_table.query(
        KeyConditionExpression=Key("guild_id").eq(guild_id)
    )

    if not response.get("Items"):
        guild_info_table.put_item(Item={"guild_id": guild_id})


def update_guild_channel(guild_id: int, channel_id: int) -> None:
    add_guild_to_db(guild_id)  # if the guild isn't in DB for some reason, adds it

    guild_info_table.update_item(
        Key={"guild_id": guild_id},
        UpdateExpression="SET channel_id = :channel_id",
        ExpressionAttributeValues={":channel_id": channel_id},
    )


if __name__ == "__main__":
    # add_guild_to_db(123)
    update_guild_channel(123, 789)
