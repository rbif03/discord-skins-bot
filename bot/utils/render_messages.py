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


if __name__ == "__main__":
    print(render_formatting_help_msg("->"))
