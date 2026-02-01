import asyncio
import logging
import time
from urllib.parse import unquote

import boto3
from boto3.dynamodb.conditions import Key

from db.exceptions import Last24hPriceNotAvailable
from models.result import Result

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
dynamodb_client = boto3.resource("dynamodb")
skin_prices_table = dynamodb_client.Table("skinsbot.skin_prices")


def get_most_recent_price_or_raise(hash_name: str) -> str:
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
        raise Last24hPriceNotAvailable(
            f"Couldn't find a price for {unquote(hash_name)} in the last 24h."
        )


async def get_most_recent_price(hash_name: str) -> Result:
    try:
        price = await asyncio.to_thread(get_most_recent_price_or_raise, hash_name)
        return Result(success=True, data={"price_usd": price})

    except Last24hPriceNotAvailable as e:
        return Result(success=False, text=str(e))

    except Exception as e:
        text = f"Failed to get most recent price for hash_name={hash_name}"
        exception_text = f"{type(e).__name__}: {e}"
        logger.error(f"{text} {exception_text}")
        return Result(success=False, text=text)


async def get_most_recent_prices(hash_names: list[str]):
    hash_name_to_price_usd_map = {}
    for hash_name in hash_names:
        price_result = await get_most_recent_price(hash_name)
        if not price_result.success:
            hash_name_to_price_usd_map[hash_name] = None
            continue

        price = price_result.data.get("price_usd")
        hash_name_to_price_usd_map[hash_name] = price
    return hash_name_to_price_usd_map
