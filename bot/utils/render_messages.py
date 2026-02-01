from urllib.parse import unquote
import discord


def render_no_active_listings_msg(COMMAND_PREFIX):
    return (
        f":cross_mark: No active listings found for that skin.\n"
        "This usually means:\n"
        f"1) The name is misspelled (see `{COMMAND_PREFIX}formatting_help`).\n"
        "2) The skin is too rare to track reliably."
    )


def render_formatting_help_msg(COMMAND_PREFIX):
    return (
        "Skin formatting help\n\n"
        "You can provide a skin in 2 ways:\n\n"
        "1) Skin name (recommended)\n"
        "Use this exact pattern:\n"
        "WEAPON | SKIN NAME (WEAR)\n\n"
        "Examples:\n"
        "`AWP | Safari Mesh (Field-Tested)`\n"
        "`AK-47 | Redline (Minimal Wear)`\n"
        "`Glock-18 | Water Elemental (Factory New)`\n\n"
        "Wear must be one of:\n"
        "`Factory New`, `Minimal Wear`, `Field-Tested`, `Well-Worn`, `Battle-Scarred`\n\n"
        "2) Steam Market link\n"
        "Paste the full listing URL, like:\n"
        "`https://steamcommunity.com/market/listings/730/StatTrak%E2%84%A2%20AUG%20%7C%20Triqua%20%28Well-Worn%29`\n\n"
        "Tips:\n"
        "- Include the wear in parentheses. It matters.\n"
        "- Keep the | between weapon and skin name.\n"
        "- Copy and paste from Steam if possible to avoid typos.\n"
        "- Some skins may be too rare and have no active listings.\n\n"
        f"Example usage:\n"
        f"{COMMAND_PREFIX}add_skin AWP | Safari Mesh (Field-Tested)\n"
        f"{COMMAND_PREFIX}add_skin `https://steamcommunity.com/market/listings/730/...`"
    )


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
        description += (
            f":small_blue_diamond: **{unquote(hash_name)}** — **${f"{price:.2f}"}**\n"
        )
    return discord.Embed(title=title, description=description, color=0x68B2FC)


if __name__ == "__main__":
    print(render_formatting_help_msg("->"))
