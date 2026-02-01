from datetime import datetime, time, timedelta, timezone


def get_shutdown_time():
    """
    Get the bot shutdown time to avoid lambda errors.

    Example:
    If the aws lambda function is called at 09:15:00, the bot should shut down
    at 09:29:50 so the lambda function can be recalled at 09:30:00.

    P.S. aws lambda functions can be executed for 15 mins at most.
    """

    utc_now = datetime.now(timezone.utc)
    n_exec = 1 + utc_now.minute // 15  # 1 to 4 scale
    return datetime(
        utc_now.year,
        utc_now.month,
        utc_now.day,
        utc_now.hour,
        15 * n_exec - 1,
        45,
        tzinfo=timezone.utc,
    )


if __name__ == "__main__":
    print(get_shutdown_time())
