"""The Länderübergreifendes Hochwasser Portal API - Functions for Mecklenburg-Vorpommern."""

from __future__ import annotations

import re

from .api_utils import (
    DynamicData,
    LHPError,
    StaticData,
    convert_to_datetime,
    convert_to_float,
    convert_to_int,
    fetch_soup,
)


def init_MV(ident: str) -> StaticData:  # pylint: disable=invalid-name
    """Init data for Mecklenburg-Vorpommern."""
    try:
        # Get data
        soup = fetch_soup("https://pegelportal-mv.de/pegel_list.html")
        table = soup.find("table", id="pegeltab")
        tbody = table.find("tbody")
        search_string = re.compile(ident[3:])
        link = tbody.find_next("a", href=search_string)
        row = link.parent.parent
        tds = row.find_all("td")
        # Parse data
        name = tds[0].getText().strip() + " / " + tds[1].getText().strip()
        if ident.find(".") != -1:
            url = "https://pegelportal-mv.de/" + ident[3:] + ".html"
        else:
            url = link["href"]
        return StaticData(ident=ident, name=name, url=url)
    except Exception as err:
        raise LHPError(err, "mv_api.py: init_MV()") from err


def update_MV(static_data: StaticData) -> DynamicData:  # pylint: disable=invalid-name
    """Update data for Mecklenburg-Vorpommern."""
    try:
        # Get data
        soup = fetch_soup("https://pegelportal-mv.de/pegel_list.html")
        table = soup.find("table", id="pegeltab")
        tbody = table.find("tbody")
        search_string = re.compile(static_data.ident[3:])
        link = tbody.find_next("a", href=search_string)
        row = link.parent.parent
        tds = row.find_all("td")
        # Parse data
        last_update = convert_to_datetime(tds[2].getText().strip(), "%d.%m.%Y %H:%M")
        level = convert_to_float(tds[3].getText().strip())
        flow = convert_to_float(tds[4].getText().strip())
        img = tds[5].find("img")
        if (img is not None) and img.has_attr("title"):
            splits = img["title"].strip().split()
            if splits[0] == "Pegel-Stufe":
                stage = convert_to_int(splits[1])
                if stage is not None:
                    stage = stage - 4
                    stage = max(stage, 0)
            else:
                stage = None
        else:
            stage = None
        return DynamicData(level=level, stage=stage, flow=flow, last_update=last_update)
    except Exception as err:
        raise LHPError(err, "mv_api.py: update_MV()") from err
