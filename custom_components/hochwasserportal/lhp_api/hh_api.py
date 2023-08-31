"""The Länderübergreifendes Hochwasser Portal API - Functions for Hamburg."""

from __future__ import annotations
from collections import namedtuple
from .api_utils import LHPError, fetch_soup
import datetime


def init_HH(ident):
    """Init data for Hamburg."""
    try:
        # Get data
        soup = fetch_soup("https://www.wabiha.de/karte.html")
        tooltipwrapper = soup.find("div", id="tooltipwrapper")
        div = tooltipwrapper.find_next("div", id="tooltip-content-" + ident[3:])
        spans = div.find_all("span")
        # Parse data
        if len(spans) == 8:
            text = div.getText()
            name = text[: text.find("Gewässer:")].strip()
            name = (
                name
                + " / "
                + text[
                    text.find("Gewässer:") + 9 : text.find("Niederschlagsvorhersage")
                ].strip()
            )
            url = "https://www.wabiha.de/grafik-" + ident[3:] + ".html"
        Initdata = namedtuple("Initdata", ["name", "url"])
        return Initdata(name, url)
    except Exception as err:
        raise LHPError(err, "hh_api.py: init_HH()") from err


def parse_HH(ident):
    """Parse data for Hamburg."""
    try:
        # Get data
        soup = fetch_soup("https://www.wabiha.de/karte.html")
        tooltipwrapper = soup.find("div", id="tooltipwrapper")
        div = tooltipwrapper.find_next("div", id="tooltip-content-" + ident[3:])
        spans = div.find_all("span")
        # Parse data
        last_update = None
        if len(spans) == 8:
            text = div.getText()
            try:
                level = float(
                    text[
                        text.find("Wasserstand")
                        + 11 : text.find("[NHN\u00A0+/-\u00A0cm]")
                    ]
                    .replace(".", "")
                    .strip()
                )
            except:
                level = None
            try:
                last_update = datetime.datetime.strptime(
                    text[
                        text.find("\u00A0\u00A0\u00A0 um") + 6 : text.find("Trend")
                    ].strip(),
                    "%d.%m.%Y %H:%M",
                )
            except:
                last_update = None
            try:
                stage_in = int(spans[7].attrs["class"][-1].split("_")[-1])
                if stage_in == 0:
                    stage = 0
                elif stage_in == 1:
                    stage = 1
                elif stage_in == 2:
                    stage = 3
                else:
                    stage = None
            except:
                stage = None
        Cyclicdata = namedtuple("Cyclicdata", ["level", "stage", "last_update"])
        return Cyclicdata(level, stage, last_update)
    except Exception as err:
        raise LHPError(err, "hh_api.py: parse_HH()") from err
