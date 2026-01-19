import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb_client = boto3.resource("dynamodb")
guild_info_table = dynamodb_client.Table("skinsbot.guild_info")
tracked_skins_table = dynamodb_client.Table("skinsbot.tracked_skins")


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


def add_to_tracked_skins(guild_id: int, hash_name: str) -> None:
    response = tracked_skins_table.query(
        KeyConditionExpression=Key("guild_id").eq(guild_id)
    )
    guild_tracked_hash_names = [
        d.get("hash_name") for d in response.get("Items") if d.get("hash_name")
    ]

    if hash_name not in guild_tracked_hash_names:
        tracked_skins_table.put_item(
            Item={"guild_id": guild_id, "hash_name": hash_name}
        )
        return


if __name__ == "__main__":
    response = tracked_skins_table.query(KeyConditionExpression=Key("guild_id").eq(13))

    print(response.get("Items"))
