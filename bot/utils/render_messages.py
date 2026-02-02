from urllib.parse import unquote
import discord


def render_no_active_listings_msg(COMMAND_PREFIX):
    return (
        f":cross_mark: No active listings found for that skin.\n"
        "This usually means:\n"
        f"1) The name is misspelled (see `{COMMAND_PREFIX}formatting_help`).\n"
        "2) The skin is too rare to track reliably."
    )


def render_help_embed(COMMAND_PREFIX: str) -> dict:
    embed_dict = {
        "title": "SkinsBot — Commands",
        "description": (
            "Track Steam Market skin prices and get periodic updates.\n\n"
            f"**Start here:** `{COMMAND_PREFIX}set_skinsbot_channel`"
        ),
        "fields": [
            {
                "name": f"{COMMAND_PREFIX}set_skinsbot_channel",
                "value": "Sets the channel where SkinsBot will post price updates. Run this first.",
                "inline": False,
            },
            {
                "name": f"{COMMAND_PREFIX}add_skin <skin name | Steam Market link>",
                "value": "Start tracking a skin’s price.",
                "inline": False,
            },
            {
                "name": f"{COMMAND_PREFIX}remove_skin <skin name>",
                "value": "Stop tracking a skin’s price.",
                "inline": False,
            },
            {
                "name": f"{COMMAND_PREFIX}tracked_skins",
                "value": "Show all skins currently being tracked in this server/channel.",
                "inline": False,
            },
            {
                "name": f"{COMMAND_PREFIX}formatting_help",
                "value": "Examples and rules for formatting skin names (recommended input method).",
                "inline": False,
            },
        ],
        "footer": {
            "text": f"Tip: Use `{COMMAND_PREFIX}formatting_help` if a skin name isn’t being recognized."
        },
    }
    return discord.Embed.from_dict(embed_dict)


def render_formatting_help_msg(COMMAND_PREFIX):
    return (
        "**Skin Name Formatting Help**\n\n"
        "You can provide an item in 2 ways:\n\n"
        "**1) Item name**\n"
        "Use one of the patterns below:\n\n"
        "```A) Cases\n"
        "Just send the case name:\n"
        "Revolution Case\n"
        "Glove Case```\n"
        "```B) Normal skins\n"
        "WEAPON | SKIN NAME (WEAR)\n"
        "Examples:\n"
        "AWP | Safari Mesh (Field-Tested)\n"
        "AK-47 | Redline (Minimal Wear)\n"
        "Glock-18 | Water Elemental (Factory New)```\n"
        "```C) Souvenir skins\n"
        "Add the `Souvenir` prefix before the weapon:\n"
        "`Souvenir WEAPON | SKIN NAME (WEAR)`\n"
        "Examples:\n"
        "Souvenir SSG 08 | Prey (Battle-Scarred)\n"
        "Souvenir Nova | Rain Station (Minimal Wear)```\n"
        "```D) StatTrak\u2122 skins\n"
        "Add the `StatTrak\u2122` prefix before the weapon.\n"
        "The `\u2122` symbol is optional.\n"
        "Important: `StatTrak` must be properly capitalized.\n"
        "Examples:\n"
        "StatTrak\u2122 FAMAS | Meow 36 (Field-Tested)\n"
        "StatTrak FAMAS | Meow 36 (Field-Tested)```\n"
        "**Wear must be one of:**\n"
        "`Factory New`, `Minimal Wear`, `Field-Tested`, `Well-Worn`, `Battle-Scarred`\n"
        "You can also use abbreviations:\n"
        "`(FN)`, `(MW)`, `(FT)`, `(WW)`, `(BS)`\n\n"
        "**2) Steam Market link**\n"
        "```Paste the full listing URL, like:\n"
        "https://steamcommunity.com/market/listings/730/StatTrak%E2%84%A2%20AUG%20%7C%20Triqua%20%28Well-Worn%29```\n"
        "Tips:\n"
        "- Include the wear in parentheses. It matters.\n"
        "- Keep the | between weapon and skin name.\n"
        "- Copy and paste from Steam if possible to avoid typos.\n"
        "- Some items may be too rare and have no active listings.\n\n"
        "**Example usage:**\n"
        f"```{COMMAND_PREFIX}add_skin AWP | Safari Mesh (FT)\n"
        f"{COMMAND_PREFIX}add_skin Souvenir SSG 08 | Prey (Battle-Scarred)\n"
        f"{COMMAND_PREFIX}add_skin StatTrak FAMAS | Meow 36 (MW)\n"
        f"{COMMAND_PREFIX}add_skin Revolution Case\n"
        f"{COMMAND_PREFIX}add_skin https://steamcommunity.com/market/listings/730/...```"
    )


def abbreviate_wear(unquoted_hash_name: str) -> str:
    abbreviations = {
        "Factory New": "FN",
        "Minimal Wear": "MW",
        "Field-Tested": "FT",
        "Well-Worn": "WW",
        "Battle-Scarred": "BS",
    }
    for full, abbr in abbreviations.items():
        if f"({full})" in unquoted_hash_name:
            return unquoted_hash_name.replace(f"({full})", f"({abbr})")
    return unquoted_hash_name


def render_skin_prices_message(hash_name_to_price_usd_map: dict):
    title = ":gem: CS2 Price Tracker :gem:"
    description = ""
    sorted_map = {
        k: v
        for k, v in sorted(
            hash_name_to_price_usd_map.items(), key=lambda item: item[1], reverse=True
        )
    }
    for hash_name, price_usd in sorted_map.items():
        price = round(float(price_usd), 2)
        unquoted_hash_name = abbreviate_wear(unquote(hash_name))
        description += (
            f":small_blue_diamond: **{unquoted_hash_name}** — **${f"{price:.2f}"}**\n"
        )
    return discord.Embed(title=title, description=description, color=0x68B2FC)


if __name__ == "__main__":
    print(render_formatting_help_msg("->"))
