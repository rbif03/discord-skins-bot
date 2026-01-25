class SkinAlreadyTrackedError(Exception):
    pass


class TrackedSkinsLimitExceededError(Exception):
    pass


class SkinNotTrackedError(Exception):
    pass


class Last24hPriceNotAvailable(Exception):
    pass
