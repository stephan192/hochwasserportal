"""The Länderübergreifendes Hochwasser Portal API - Functions for Bayern."""

from __future__ import annotations
from collections import namedtuple
from .api_utils import fetch_soup
import datetime


def init_BY(ident):
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
        Initdata = namedtuple("Initdata", ["name", "url"])
        return Initdata(name, url)
    except Exception as err_msg:
        Initdata = namedtuple("Initdata", ["err_msg"])
        return Initdata(err_msg)


def parse_BY(ident):
    """Parse data for Bayern."""
    try:
        # Get data
        soup = fetch_soup("https://www.hnd.bayern.de/pegel")
        img_id = "p" + ident[3:]
        imgs = soup.find_all("img", id=img_id)
        data = imgs[0]
        # Parse data
        if len(data.get("data-wert")) > 0:
            level = float(str(data.get("data-wert")).replace(",", "."))
        else:
            level = None
        if len(data.get("data-wert2")) > 0:
            flow = float(str(data.get("data-wert2")).replace(",", "."))
        else:
            flow = None
        if len(data.get("data-ms")) > 0:
            stage = int(data.get("data-ms"))
        else:
            stage = None
        hint = data.get("data-stoerung")
        if len(data.get("data-datum")) > 0:
            try:
                last_update = datetime.datetime.strptime(
                    data.get("data-datum"), "%d.%m.%Y, %H:%M"
                )
            except:
                last_update = None
        else:
            last_update = None
        Cyclicdata = namedtuple(
            "Cyclicdata", ["level", "stage", "flow", "last_update", "hint"]
        )
        return Cyclicdata(level, stage, flow, last_update, hint)
    except Exception as err_msg:
        Cyclicdata = namedtuple("Cyclicdata", ["err_msg"])
        return Cyclicdata(err_msg)
