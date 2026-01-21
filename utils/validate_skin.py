from dataclasses import dataclass
from typing import Literal

import requests
from requests.exceptions import JSONDecodeError, RequestException
import time
from urllib.parse import quote, unquote

APP_ID = 730  # CS2 app id
USD_ID = 1


@dataclass
class SkinValidator:
    hash_name: str = ""
    validation_status: Literal["success", "error"]
    message: str = ""
    unquoted_hash_name: str = ""


class UnsuccessfulRequestError(Exception):
    pass


def iter_hash_name_candidates(message: str):
    STEAM_MARKET_PREFIX = "steamcommunity.com/market/listings/730/"
    if STEAM_MARKET_PREFIX in message:
        raw = message.split(STEAM_MARKET_PREFIX, 1)[1]
        # Don't escape '%': if the URL already has '%20'/'%7C', we avoid double-encoding. Assumes '%' means "already encoded"; would break if an item name ever contains a literal '%'.
        quoted = quote(raw, safe="%")

        # Try "as-is" first, then quoted only if it changes anything
        yield raw
        if quoted != raw:
            yield quoted
    else:
        # For plain skin names, just quote once (no second request)
        yield quote(message)


def get_listings(hash_name: str) -> dict:
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
    endpoint = f"https://steamcommunity.com/market/listings/{APP_ID}/{hash_name}/render"
    params = {"currency": USD_ID, "start": 0}
    response = requests.get(endpoint, params=params)

    if response.status_code != 200:
        raise UnsuccessfulRequestError(
            f"Request was not successful. "
            f"STATUS CODE {response.status_code}: "
            f"{response.text}"
        )

    response_json = response.json()
    return response_json


def response_has_active_listings(get_listings_response_json: dict) -> bool:
    listinginfo = get_listings_response_json.get("listinginfo", {})
    if not listinginfo:
        return False

    if not isinstance(listinginfo, dict):
        return False

    listing_ids = listinginfo.keys()
    if not listing_ids:
        return False

    return True


def get_listings_try_excepts(hash_name: str, command_prefix: str) -> SkinValidator:
    try:
        resp = get_listings(hash_name)

    except (RequestException, JSONDecodeError, UnsuccessfulRequestError) as e:
        return SkinValidator(
            hash_name=hash_name,
            validation_status="error",
            message=(
                ":cross_mark: Couldn't validate that skin right now.\n"
                "This is usually a temporary Steam Market/API issue — please try again in a bit.\n"
                f"You can also double-check the spelling/format (see `{command_prefix}formatting_help`)."
                f"`{e}`"
            ),
        )

    if not response_has_active_listings(resp):
        return SkinValidator(
            hash_name=hash_name,
            validation_status="error",
            message=(
                f":cross_mark: No active listings found for that skin.\n"
                "This usually means:\n"
                f"1) The name is misspelled (see `{command_prefix}formatting_help`).\n"
                "2) The skin is too rare to track reliably."
            ),
        )

    return SkinValidator(
        hash_name=hash_name,
        validation_status="success",
        unquoted_hash_name=unquote(hash_name),
    )


def get_SkinValidator_obj(message: str, command_prefix: str) -> dict:
    candidates = list(iter_hash_name_candidates(message))
    max_requests_value = len(candidates) - 1

    for i, hash_name in enumerate(candidates):
        SkinValidator_obj = get_listings_try_excepts(hash_name, command_prefix)

        if SkinValidator_obj.validation_status == "success":
            return SkinValidator_obj

        # only sleep if we're actually going to make another request
        if i < max_requests_value:
            time.sleep(1)

    return SkinValidator_obj


if __name__ == "__main__":
    import json

    print(
        json.dumps(
            get_listings("AWP | Safari Mesh (Field-Tested)")["body"]["listinginfo"],
            indent=4,
        )
    )
