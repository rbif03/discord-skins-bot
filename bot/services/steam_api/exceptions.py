class UnsuccessfulRequestError(Exception):
    """
    Raised when a Steam API request returns a non-200 status code.
    """

    pass


class InvalidSteamMarketListingsUrlError(Exception):
    pass


class NoActiveListingsError(Exception):
    pass


class SteamMarketRequestError(Exception):
    text = (
        ":cross_mark: Couldn't validate that skin right now.\n"
        "This is usually a temporary Steam Market/API issue — please try again in a bit.\n"
        "You can also double-check the spelling/format (see `->formatting_help`)."
    )
