from decimal import Decimal
import logging
import time
from typing import Union

import boto3
import requests
from requests.exceptions import JSONDecodeError, RequestException
from tenacity import retry, stop_after_attempt, wait_fixed

dynamodb_client = boto3.resource("dynamodb")
skin_prices_table = dynamodb_client.Table("skinsbot.skin_prices")
tracked_skins_table = dynamodb_client.Table("skinsbot.tracked_skins")

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class UnsuccessfulRequestError(Exception):
    pass


class NoInfoFoundError(Exception):
    pass


class DynamodbError(Exception):
    pass


def add_params_to_url(url: str, params: dict[str : Union[int, str]]):
    """
    Append query params to `url` *without* encoding them.

    Used when values (e.g., Steam `market_hash_name`) are already percent-encoded;
    passing them via `requests.get(..., params=...)` would double-encode `%` (-> `%25`).
    """
    if url[-1] != "/":
        url += "/"
    url += "?"
    params_str = "&".join([f"{k}={v}" for k, v in params.items()])
    return url + params_str


@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
def get_market_price_overview(hash_name: str):
    """
    Fetch Steam Market `priceoverview` data for a CS2 item.

    Response body:
        - success (bool): request succeeded and Steam recognized the item
        - lowest_price (str): lowest active listing price (e.g., $3.47)
        - volume (str): units sold in the last 24 hours (e.g., '10')
        - median_price (str): median sale price in the last hour (e.g., '$3.46')

    Note:
        `market_hash_name` may already be percent-encoded; we build the URL manually to
        avoid double-encoding when using the `params` kwarg of `requests.get()`.
    """
    url = "https://steamcommunity.com/market/priceoverview/"
    params = {
        "appid": 730,  # CS2 appid
        "currency": 1,  # USD
        "market_hash_name": hash_name,
    }

    url = add_params_to_url(url, params)
    response = requests.get(url)

    if response.status_code != 200:
        raise UnsuccessfulRequestError(
            f"Unsuccessful response for hash_name={hash_name}. status_code={response.status_code}"
        )

    if response.json() == {"success": True}:
        raise NoInfoFoundError(f"No price info found for hash_name={hash_name}")

    return {
        "status": response.status_code,
        "body": response.json(),
        "text": response.text,
    }


def convert_price_to_decimal(price: str):
    return Decimal(price.replace("$", ""))


def add_price_to_dynamodb(hash_name: str, price: float, unix_now: int):
    try:
        skin_prices_table.put_item(
            Item={
                "hash_name": hash_name,
                "unix_timestamp": unix_now,
                "price_usd": price,
            }
        )
        logger.info(f"hash_name={hash_name}; unix_timestamp={unix_now} added to db!")
    except Exception as e:
        raise DynamodbError(str(e))


def handler(event, context):
    hash_names = event.get("hash_names", [])
    consecutive_errors = 0
    for hash_name in hash_names:
        if consecutive_errors >= 3:
            logger.critical("Can't fetch or add any skin prices to db. Shutting down.")
            break

        try:
            unix_now = int(time.time())
            price_overview = get_market_price_overview(hash_name)
            logging.info(f"{hash_name} price_overview:{price_overview.get('body')}")

            cheapest_listing = convert_price_to_decimal(
                price_overview["body"]["lowest_price"]
            )

            add_price_to_dynamodb(hash_name, cheapest_listing, unix_now)
            consecutive_errors = 0

        except RequestException as e:
            consecutive_errors += 1
            logger.error(
                f"Failed to fetch price overview for hash_name={hash_name}. {e}"
            )
        except JSONDecodeError as e:
            consecutive_errors += 1
            logger.error(f"Failed to decode response for hash_name={hash_name}. {e}")
        except (UnsuccessfulRequestError, NoInfoFoundError) as e:
            consecutive_errors += 1
            logger.error(str(e))
        except DynamodbError as e:
            consecutive_errors += 1
            logger.error(f"Failed to add hash_name={hash_name} to db. {e}")
        except Exception as e:
            consecutive_errors += 1
            logger.error(str(e))

        time.sleep(5)

    return


if __name__ == "__main__":
    from urllib.parse import quote

    hash_names = [
        "AWP | Redline (Field-Tested)",
        "AK-47 | Slate (Minimal Wear)",
        "USP-S | Blueprint (Field-Tested)",
        "Glock-18 | Bunsen Burner (Minimal Wear)",
    ]
    event = {"hash_names": [quote(hn) for hn in hash_names]}
    handler(event, None)
