"""The Länderübergreifendes Hochwasser Portal API - Functions for Thüringen."""

from __future__ import annotations

from .api_utils import (
    DynamicData,
    LHPError,
    StaticData,
    convert_to_datetime,
    convert_to_float,
    fetch_soup,
)


def init_TH(ident: str) -> StaticData:  # pylint: disable=invalid-name
    """Init data for Thüringen."""
    try:
        # Get data
        soup = fetch_soup("https://hnz.thueringen.de/hw-portal/thueringen.html")
        table = soup.find_all("table", id="pegelTabelle")[0]
        tbody = table.find_all("tbody")[0]
        trs = tbody.find_all("tr")
        # Parse data
        for row in trs:
            tds = row.find_all("td")
            if len(tds) > 10:
                if tds[1].getText().strip() != ident[3:]:
                    continue
                links = tds[1].find_all("a")
                url = "https://hnz.thueringen.de" + links[0]["href"]
                name = tds[2].getText().strip() + " / " + tds[3].getText().strip()
                return StaticData(ident=ident, name=name, url=url)
        return StaticData(ident=ident)
    except Exception as err:
        raise LHPError(err, "th_api.py: init_TH()") from err


def update_TH(static_data: StaticData) -> DynamicData:  # pylint: disable=invalid-name
    """Update data for Thüringen."""
    level = None
    flow = None
    try:
        # Get data
        soup = fetch_soup("https://hnz.thueringen.de/hw-portal/thueringen.html")
        table = soup.find_all("table", id="pegelTabelle")[0]
        tbody = table.find_all("tbody")[0]
        trs = tbody.find_all("tr")
        # Parse data
        for row in trs:
            tds = row.find_all("td")
            if len(tds) > 10:
                if tds[1].getText().strip() != static_data.ident[3:]:
                    continue
                last_update = convert_to_datetime(
                    tds[7].getText().strip(), "%d.%m.%Y %H:%M"
                )
                level = convert_to_float(tds[8].getText().strip(), True)
                flow = convert_to_float(tds[10].getText().strip(), True)
                return DynamicData(level=level, flow=flow, last_update=last_update)
        return DynamicData()
    except Exception as err:
        raise LHPError(err, "th_api.py: update_TH()") from err
