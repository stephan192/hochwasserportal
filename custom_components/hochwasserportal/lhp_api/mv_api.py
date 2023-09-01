"""The Länderübergreifendes Hochwasser Portal API - Functions for Mecklenburg-Vorpommern."""

from __future__ import annotations

import re
from datetime import datetime

from .api_utils import DynamicData, LHPError, StaticData, fetch_soup


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
        cnt = 0
        for tdata in tds:
            if cnt == 0:
                name = tdata.getText().strip()
            elif cnt == 1:
                name += " / " + tdata.getText().strip()
                break
            cnt += 1
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
        cnt = 0
        for tdata in tds:
            if cnt == 2:
                try:
                    last_update = datetime.strptime(
                        tdata.getText().strip(), "%d.%m.%Y %H:%M"
                    )
                except:
                    last_update = None
            elif cnt == 3:
                try:
                    level = float(tdata.getText().strip())
                except:
                    level = None
            elif cnt == 4:
                try:
                    flow = float(tdata.getText().strip())
                except:
                    flow = None
                img = tdata.find_next("img")
                try:
                    splits = img["title"].strip().split()
                    if splits[0] == "Pegel-Stufe":
                        stage = int(splits[1]) - 4
                        stage = max(stage, 0)
                    else:
                        stage = None
                except:
                    stage = None
                break
            cnt += 1
        return DynamicData(level=level, stage=stage, flow=flow, last_update=last_update)
    except Exception as err:
        raise LHPError(err, "mv_api.py: update_MV()") from err
