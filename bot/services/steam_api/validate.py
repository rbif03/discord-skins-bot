import asyncio
import logging
from urllib.parse import quote, unquote, urlparse

import requests
from requests.exceptions import JSONDecodeError, RequestException

from models.result import Result
from services.steam_api.exceptions import (
    InvalidSteamMarketListingsUrlError,
    NoActiveListingsError,
    SteamMarketRequestError,
    UnsuccessfulRequestError,
)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def translate_wear_abbreviation_to_full(command_argument: str) -> str:
    abbreviations = {
        "FN": "Factory New",
        "MW": "Minimal Wear",
        "FT": "Field-Tested",
        "WW": "Well-Worn",
        "BS": "Battle-Scarred",
    }
    for abbr, full in abbreviations.items():
        if f"({abbr})" in command_argument:
            return command_argument.replace(f"({abbr})", f"({full})")

    return command_argument


def fix_stattrak_typo(command_argument: str) -> str:
    if "StatTrak " in command_argument:
        return command_argument.replace("StatTrak ", "StatTrak™ ")
    return command_argument


def get_hash_name_or_raise(command_argument: str) -> str:
    """
    Extracts the Steam Market hash name from either:
      - A plain item name (e.g. "P250 | Supernova (Factory New)"), or
      - A Steam Market listing URL containing a URL-encoded name
        (e.g. "https://steamcommunity.com/market/listings/730/P250%20%7C%20Supernova%20(Factory%20New)").
    """
    parsed = urlparse(command_argument)
    if not parsed.scheme and not parsed.netloc:
        # It's not a URL
        command_argument = translate_wear_abbreviation_to_full(command_argument)
        command_argument = fix_stattrak_typo(command_argument)
        return quote(command_argument)

    if "steamcommunity.com" in parsed.netloc and "/market/listings/730/" in parsed.path:
        # It's a URL, extract the path and return the hash name
        path_segments = parsed.path.split("/")
        try:
            path_segments.remove("")
            return path_segments[3]
        except (ValueError, KeyError) as e:
            raise InvalidSteamMarketListingsUrlError("Invalid Steam Market URL.")

    raise InvalidSteamMarketListingsUrlError("Invalid Steam Market URL.")


def get_hash_name(command_argument: str) -> Result:
    try:
        hash_name = get_hash_name_or_raise(command_argument)
        return Result(success=True, data={"hash_name": hash_name})

    except InvalidSteamMarketListingsUrlError as e:
        return Result(success=False, text=str(e))


def get_listings_or_raise(hash_name: str) -> dict:
    """
    Fetch Steam Market listing data for `hash_name`.

    Args:
        hash_name: The Steam Market hash name (URL-encoded) for the item.

    Returns:
        The parsed JSON response as a dict.

    Raises:
        UnsuccessfulRequestError: If the request status_code != 200
        requests.exceptions.RequestException: If the request fails (e.g., network/timeout/connection issues).
        requests.exceptions.JSONDecodeError: If the response body cannot be decoded as JSON.
    """
    endpoint = f"https://steamcommunity.com/market/listings/730/{hash_name}/render"
    params = {"currency": 1, "start": 0}  # currency 1 is USD
    response = requests.get(endpoint, params=params)

    if response.status_code != 200:
        raise UnsuccessfulRequestError(
            f"Request was not successful. "
            f"STATUS CODE {response.status_code}: "
            f"{response.text}"
        )

    response_json = response.json()
    return response_json


def is_listings_response_valid(listings_response: dict) -> bool:
    listinginfo = listings_response.get("listinginfo", {})
    if not listinginfo:
        return False

    if not isinstance(listinginfo, dict):
        return False

    listing_ids = listinginfo.keys()
    if not listing_ids:
        return False

    return True


def validate_listings_response_or_raise(listings_response: dict) -> None:
    if not is_listings_response_valid(listings_response):
        raise NoActiveListingsError(
            f":cross_mark: No active listings found for that skin.\n"
            "This usually means:\n"
            f"1) The name is misspelled (see `->formatting_help`).\n"
            "2) The skin is too rare to track reliably."
        )


async def validate_add_skin_argument(command_argument: str) -> Result:
    try:
        hash_name = get_hash_name_or_raise(command_argument)
        listings_response = await asyncio.to_thread(get_listings_or_raise, hash_name)
        validate_listings_response_or_raise(listings_response)
        return Result(success=True, data={"hash_name": hash_name})

    except InvalidSteamMarketListingsUrlError as e:
        return Result(success=False, text=str(e))

    except (JSONDecodeError, RequestException) as e:
        logger.error(str(e))
        raise SteamMarketRequestError

    except UnsuccessfulRequestError as e:
        logger.error(str(e))
        raise SteamMarketRequestError

    except SteamMarketRequestError as e:
        return Result(success=False, text=e.text)

    except NoActiveListingsError as e:
        return Result(success=False, text=str(e))

    except Exception as e:
        logger.error(str(e))
        return Result(success=False, text=SteamMarketRequestError.text)
