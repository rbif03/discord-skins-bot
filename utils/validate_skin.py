import requests
from urllib.parse import quote, unquote

APP_ID = 730  # CS2 app id
USD_ID = 1


def get_hash_name_from_message(message: str, quote_steam_url=False) -> str:
    # function to check if message is like the url below
    # url_example = "https://steamcommunity.com/market/listings/730/{anything_here}"
    steam_market_url = "steamcommunity.com/market/listings/730/"
    if steam_market_url in message:
        hash_name = message.split(steam_market_url, 1)[1]
        if quote_steam_url:
            hash_name = quote(hash_name)
    else:
        hash_name = quote(message)

    return hash_name


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


def validate_skin_from_message(message: str) -> bool:
    """
    Return whether the Steam Market item in `message` has active listings.

    Tries once assuming the URL is already quoted; if no listings are found, retries
    once with quoting enabled.
    """
    for quote_enabled in (False, True):
        hash_name = get_hash_name_from_message(message, quote_steam_url=quote_enabled)
        resp = get_listings(hash_name)
        if response_has_active_listings(resp):
            return {"is_valid": True, "hash_name": hash_name}
    return {"is_valid": False}


if __name__ == "__main__":
    pass
