import requests
from requests.exceptions import JSONDecodeError
import json
import urllib.parse
from typing import Literal

ValidWear = Literal["FN", "MW", "FT", "WW", "BS"]

DEFAULT_URL = "https://www.steamcommunity.com"


def add_params_to_url(url: str, params: dict):
    url = url[:-1] if url[-1] in ("/", "?") else url
    url += "?"
    for param_idx, param_tuple in enumerate(params.items()):
        if param_idx != 0:
            url += "&"
        param_name, param_val = param_tuple
        url += f"{param_name}={param_val}"
    return url


def get_hash_name(item: str, skin: str, wear: ValidWear, stat: bool):
    item = item.replace(" ", "%20")
    skin = skin.replace(" ", "%20")
    float = {
        "FN": "%20%28Factory%20New%29",
        "MW": "%20%28Minimal%20Wear%29",
        "FT": "%20%28Field-Tested%29",
        "WW": "%20%28Well-Worn%29",
        "BS": "%20%28Battle-Scarred%29",
    }
    wear = float[wear]
    if stat == True:
        item = "StatTrak%E2%84%A2%20" + item
    hash_name = item + "%20%7C%20" + skin + wear
    return hash_name


def get_market_price_overview(market_hash_name: str):
    path = "/market/priceoverview"
    params = {
        "appid": 730,  # CS2 appid
        "currency": 7,  # BRL
        "market_hash_name": market_hash_name,
    }

    url = DEFAULT_URL + path
    url = add_params_to_url(url, params)
    response = requests.get(url)
    try:
        response_json = response.json()
    except JSONDecodeError:
        response_json = {}

    return {
        "status": response.status_code,
        "body": response_json,
        "text": response.text,
    }


def get_tags_map(cs2_item: dict):
    if tags := cs2_item.get("tags"):
        return {tag["category"]: tag["localized_tag_name"] for tag in tags}
    return {}


def get_items_from_inv_response(response_json: dict):
    cs2_items = list()
    for cs2_item in response_json.get("descriptions"):
        if hash_name := cs2_item.get("market_hash_name"):
            item_info = get_tags_map(cs2_item)
            if cs2_item.get("tradable") == 1:
                # URL encode the hash name
                encoded_hash_name = urllib.parse.quote(hash_name)
                item_info["market_hash_name"] = encoded_hash_name
                cs2_items.append(item_info)
    return cs2_items


def get_inventory_items(steamid: str):
    appid = 730  # CS2 appid
    contextid = 2  # contextid for the main CS/CS2 item inventory
    path = f"/inventory/{steamid}/{appid}/{contextid}"
    url = DEFAULT_URL + path

    response = requests.get(url)
    if response.status_code != 200:
        print(f"HTTP {response.status_code}: {response.text}")
        return None
    response_json = response.json()
    cs2_items = get_items_from_inv_response(response_json)
    return cs2_items


if __name__ == "__main__":
    print(get_market_price_overview("AWP%20%7C%20Redline%20%28Minimal%20Wear%29"))
