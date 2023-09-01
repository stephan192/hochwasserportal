"""The Länderübergreifendes Hochwasser Portal API - Functions for Thüringen."""

from __future__ import annotations

from datetime import datetime

from .api_utils import DynamicData, LHPError, StaticData, fetch_soup


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
            cnt = 0
            for tdata in tds:
                if (cnt == 1) and (tdata.getText().strip() != ident[3:]):
                    break
                if cnt == 1:
                    links = tdata.find_all("a")
                    url = "https://hnz.thueringen.de" + links[0]["href"]
                elif cnt == 2:
                    name = tdata.getText().strip()
                elif cnt == 3:
                    name += " / " + tdata.getText().strip()
                    break
                cnt += 1
            if cnt == 3:
                break
        return StaticData(ident=ident, name=name, url=url)
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
        last_update_str = None
        for row in trs:
            tds = row.find_all("td")
            cnt = 0
            for tdata in tds:
                if (cnt == 1) and (tdata.getText().strip() != static_data.ident[3:]):
                    break
                if cnt == 7:
                    last_update_str = tdata.getText().strip()
                elif cnt == 8:
                    level = float(tdata.getText().strip().replace(",", "."))
                elif cnt == 10:
                    flow = float(tdata.getText().strip().replace(",", "."))
                    break
                cnt += 1
            if cnt == 10:
                break
        if last_update_str is not None:
            last_update = datetime.strptime(last_update_str, "%d.%m.%Y %H:%M")
        else:
            last_update = None
        return DynamicData(level=level, flow=flow, last_update=last_update)
    except Exception as err:
        raise LHPError(err, "th_api.py: update_TH()") from err
