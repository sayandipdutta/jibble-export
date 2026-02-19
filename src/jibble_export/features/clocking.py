import logging
import http
import datetime as dt
from jibble_export.client import AuthorizedJibbleClient
from pprint import pprint
from uuid import uuid4


def get_utc_offset() -> str:
    delta = dt.datetime.now().astimezone().utcoffset()
    if delta is None:
        return "PT0H0M"
    total_seconds = delta.total_seconds()
    sign = "-" if total_seconds < 0 else ""
    total_minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(total_minutes, 60)
    return f"{sign}PT{int(hours)}H{int(minutes)}M"


UTC_OFFSET = get_utc_offset()


def clock_in() -> None:
    client = AuthorizedJibbleClient()
    resp = client.post(
        subdomain="time-tracking",
        relative_path="/v1/TimeEntries",
        payload={
            "type": "In",
            "personId": client.auth.personId,
            "clientType": "Web",
            "offset": UTC_OFFSET,
            "time": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "platform": {
                "deviceName": "Firefox",
                "deviceModel": None,
                "clientVersion": "147.0",
                "os": "Linux",
            },
            "id": str(uuid4()),
        },
        response_model=type(None),
        status=http.HTTPStatus.CREATED,
    )
    logging.info("Successfully Jibbled in!")
    return resp


def clock_out() -> None:
    client = AuthorizedJibbleClient()
    resp = client.post(
        subdomain="time-tracking",
        relative_path="/v1/TimeEntries",
        payload={
            "type": "Out",
            "personId": client.auth.personId,
            "clientType": "Web",
            "offset": UTC_OFFSET,
            "platform": {
                "deviceName": "Firefox",
                "deviceModel": None,
                "clientVersion": "147.0",
                "os": "Linux",
            },
            "id": str(uuid4()),
        },
        response_model=type(None),
        status=http.HTTPStatus.CREATED,
    )
    logging.info("Successfully Jibbled out!")
    return resp


if __name__ == "__main__":
    resp = clock_in()
    pprint(resp)
