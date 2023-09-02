"""The Länderübergreifendes Hochwasser Portal API - Functions for Berlin."""

from __future__ import annotations

from datetime import date, timedelta

from .api_utils import (
    DynamicData,
    LHPError,
    StaticData,
    convert_to_datetime,
    convert_to_float,
    fetch_soup,
    fetch_text,
)


def init_BE(ident: str) -> StaticData:  # pylint: disable=invalid-name
    """Init data for Berlin."""
    try:
        # Get data
        page = fetch_soup(
            "https://wasserportal.berlin.de/start.php?anzeige=tabelle_ow&messanzeige=ms_ow_berlin",
            remove_xml=True,
        )
        # Parse data
        table = page.find("table", id="pegeltab")
        tbody = table.find("tbody")
        trs = tbody.find_all("tr")
        for row in trs:
            tds = row.find_all("td")
            if len(tds) == 10:
                if (tds[0].getText().strip() == ident[3:]) and (
                    tds[0].find_next("a")["href"][:12] == "station.php?"
                ):
                    url = (
                        "https://wasserportal.berlin.de/"
                        + tds[0].find_next("a")["href"]
                    )
                    name = tds[1].getText().strip() + " / " + tds[4].getText().strip()
                    return StaticData(ident=ident, name=name, url=url)
        return StaticData(ident=ident)
    except Exception as err:
        raise LHPError(err, "be_api.py: init_BE()") from err


def update_BE(static_data: StaticData) -> DynamicData:  # pylint: disable=invalid-name
    """Update data for Berlin."""
    try:
        # Get data and parse level data
        yesterday = date.today() - timedelta(days=1)
        query = (
            static_data.url
            + "&sreihe=ew&smode=c&sdatum="
            + yesterday.strftime("%d.%m.%Y")
        )
        data = fetch_text(query)
        lines = data.split("\n")
        lines.reverse()
        level = None
        last_update = None
        for line in lines:
            if len(line) > 0:
                values = line.split(";")
                if len(values) == 2:
                    level = convert_to_float(values[1], True)
                    if (level is not None) and (int(level) != -777):
                        last_update = convert_to_datetime(values[0], "%d.%m.%Y %H:%M")
                    if (level is not None) and (last_update is not None):
                        break
        # Get data and parse flow data
        query = query.replace("thema=ows", "thema=odf")
        query = query.replace("thema=wws", "thema=wdf")
        data = fetch_text(query)
        lines = data.split("\n")
        lines.reverse()
        flow = None
        for line in lines:
            if len(line) > 0:
                values = line.split(";")
                if len(values) == 2:
                    flow = convert_to_float(values[1], True)
                    if (
                        (flow is not None)
                        and (int(flow) != -777)
                        and (last_update is None)
                    ):
                        last_update = convert_to_datetime(values[0], "%d.%m.%Y %H:%M")
                    if (flow is not None) and (last_update is not None):
                        break
        return DynamicData(level=level, flow=flow, last_update=last_update)
    except Exception as err:
        raise LHPError(err, "be_api.py: update_BE()") from err
