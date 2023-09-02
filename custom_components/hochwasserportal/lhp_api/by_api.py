"""The Länderübergreifendes Hochwasser Portal API - Functions for Bayern."""

from __future__ import annotations

from .api_utils import (
    DynamicData,
    LHPError,
    StaticData,
    convert_to_datetime,
    convert_to_float,
    convert_to_int,
    fetch_soup,
)


def init_BY(ident: str) -> StaticData:  # pylint: disable=invalid-name
    """Init data for Bayern."""
    try:
        # Get data
        soup = fetch_soup("https://www.hnd.bayern.de/pegel")
        img_id = "p" + ident[3:]
        imgs = soup.find_all("img", id=img_id)
        data = imgs[0]
        # Parse data
        name = data.get("data-name")
        if len(data.get("data-zeile2")) > 0:
            name += " / " + data.get("data-zeile2")
        url = data.parent.attrs["href"]
        hint = data.get("data-stoerung")
        return StaticData(ident=ident, name=name, url=url, hint=hint)
    except Exception as err:
        raise LHPError(err, "by_api.py: init_BY()") from err


def update_BY(static_data: StaticData) -> DynamicData:  # pylint: disable=invalid-name
    """Update data for Bayern."""
    try:
        # Get data
        soup = fetch_soup("https://www.hnd.bayern.de/pegel")
        img_id = "p" + static_data.ident[3:]
        imgs = soup.find_all("img", id=img_id)
        data = imgs[0]
        # Parse data
        if len(data.get("data-wert")) > 0:
            level = convert_to_float(str(data.get("data-wert")), True)
        else:
            level = None
        if len(data.get("data-wert2")) > 0:
            flow = convert_to_float(str(data.get("data-wert2")), True)
        else:
            flow = None
        if len(data.get("data-ms")) > 0:
            stage = convert_to_int(data.get("data-ms"))
        else:
            stage = None
        if len(data.get("data-datum")) > 0:
            last_update = convert_to_datetime(data.get("data-datum"), "%d.%m.%Y, %H:%M")
        else:
            last_update = None
        return DynamicData(level=level, stage=stage, flow=flow, last_update=last_update)
    except Exception as err:
        raise LHPError(err, "by_api.py: update_BY()") from err
