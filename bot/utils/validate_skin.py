import requests
from requests.exceptions import JSONDecodeError, RequestException
import time
from urllib.parse import quote, unquote

from models.validation_response import SkinValidationResponse

APP_ID = 730  # CS2 app id
USD_ID = 1


class UnsuccessfulRequestError(Exception):
    pass


class SteamMarketRequestError(Exception):
    user_message = (
        ":cross_mark: Couldn't validate that skin right now.\n"
        "This is usually a temporary Steam Market/API issue — please try again in a bit.\n"
        "You can also double-check the spelling/format (see `->formatting_help`)."
    )


class NoActiveListingsError(Exception):
    user_message = (
        f":cross_mark: No active listings found for that skin.\n"
        "This usually means:\n"
        f"1) The name is misspelled (see `->formatting_help`).\n"
        "2) The skin is too rare to track reliably."
    )


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
    print(f"requests.get({endpoint})")
    print(f"params = {params}")

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
        raise NoActiveListingsError

    if not isinstance(listinginfo, dict):
        raise NoActiveListingsError

    listing_ids = listinginfo.keys()
    if not listing_ids:
        raise NoActiveListingsError

    return listinginfo


def fetch_listings_or_raise(hash_name: str):
    try:
        return get_listings(hash_name)

    except (RequestException, JSONDecodeError, UnsuccessfulRequestError) as e:
        raise SteamMarketRequestError(f"{e}") from e


def validate_listings_response(hash_name: str, resp) -> SkinValidationResponse:
    try:
        response_has_active_listings(resp)
        return SkinValidationResponse(hash_name=hash_name, status="success")

    except NoActiveListingsError as e:
        return SkinValidationResponse(
            hash_name=hash_name,
            status="error",
            text=e.user_message,
        )

    except Exception as e:
        return SkinValidationResponse(
            hash_name=hash_name,
            status="error",
            text=str(e),
        )


def get_listings_try_excepts(hash_name: str) -> SkinValidationResponse:
    """
    Orchestrator: fetch then validate, mapping SteamMarketRequestError to user-facing message.
    """
    try:
        resp = fetch_listings_or_raise(hash_name)

        # Exceptions in `validate_listings_response` are handled internally.
        return validate_listings_response(hash_name, resp)

    # The exceptions below are meant to catch anything raised by fetch_listings_or_raise
    except SteamMarketRequestError as e:
        return SkinValidationResponse(
            hash_name=hash_name,
            status="error",
            text=f"{e.user_message}\n{e}",
        )

    except Exception as e:
        return SkinValidationResponse(
            hash_name=hash_name,
            status="error",
            text=str(e),
        )


def get_SkinValidationResponse(message: str) -> SkinValidationResponse:
    candidates = list(iter_hash_name_candidates(message))
    max_requests_value = len(candidates) - 1

    for i, hash_name in enumerate(candidates):
        SkinValidationResponse_obj = get_listings_try_excepts(hash_name)

        if SkinValidationResponse_obj.status == "success":
            return SkinValidationResponse_obj

        # only sleep if we're actually going to make another request
        if i < max_requests_value:
            time.sleep(5)

    return SkinValidationResponse_obj


if __name__ == "__main__":
    import json

    print(
        json.dumps(
            get_listings("AWP | Safari Mesh (Field-Tested)")["body"]["listinginfo"],
            indent=4,
        )
    )
