import requests
import time
from urllib.parse import quote

APP_ID = 730  # CS2 app id
USD_ID = 1


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
    endpoint = f"https://steamcommunity.com/market/listings/{APP_ID}/{hash_name}/render"
    params = {"currency": USD_ID, "start": 0}

    response = requests.get(endpoint, params=params)
    try:
        response_json = response.json()
    except requests.exceptions.JSONDecodeError:
        print("JSONDecodeError")
        response_json = {}

    return {"status": response.status_code, "body": response_json}


def response_has_active_listings(get_listings_response: dict) -> bool:
    if get_listings_response.get("status") != 200:
        return False

    body = get_listings_response.get("body", {})
    if not body or not isinstance(body, dict):
        return False

    listinginfo = body.get("listinginfo", {})
    if not isinstance(listinginfo, dict):
        return False

    listing_ids = listinginfo.keys()
    if not listing_ids:
        return False

    return True


def validate_skin_from_message(message: str) -> dict:
    candidates = list(iter_hash_name_candidates(message))

    for i, hash_name in enumerate(candidates):
        resp = get_listings(hash_name)
        if response_has_active_listings(resp):
            return {"is_valid": True, "hash_name": hash_name}

        # only sleep if we're actually going to make another request
        if i < len(candidates) - 1:
            time.sleep(1)

    return {"is_valid": False}


if __name__ == "__main__":
    pass
