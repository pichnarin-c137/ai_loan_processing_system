from datetime import date, datetime, timedelta, timezone

CAMBODIA = timezone(timedelta(hours=7), "ICT")


def today() -> date:
    return datetime.now(CAMBODIA).date()
