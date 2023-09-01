"""The Länderübergreifendes Hochwasser Portal API - Functions for Berlin."""

from __future__ import annotations
from .api_utils import LHPError, StaticData, DynamicData, fetch_soup, fetch_text
import datetime


def init_BE(ident) -> StaticData:
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
        for tr in trs:
            tds = tr.find_all("td")
            if len(tds) == 10:
                if (tds[0].getText().strip() == ident[3:]) and (
                    tds[0].find_next("a")["href"][:12] == "station.php?"
                ):
                    url = (
                        "https://wasserportal.berlin.de/"
                        + tds[0].find_next("a")["href"]
                    )
                    name = tds[1].getText().strip() + " / " + tds[4].getText().strip()
                    break
        return StaticData(ident=ident, name=name, url=url)
    except Exception as err:
        raise LHPError(err, "be_api.py: init_BE()") from err


def update_BE(url) -> DynamicData:
    """Update data for Berlin."""
    try:
        # Get data and parse level data
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        query = url + "&sreihe=ew&smode=c&sdatum=" + yesterday.strftime("%d.%m.%Y")
        data = fetch_text(query)
        lines = data.split("\n")
        lines.reverse()
        level = None
        last_update = None
        for line in lines:
            if len(line) > 0:
                values = line.split(";")
                if len(values) == 2:
                    try:
                        level = float(values[1].replace(",", "."))
                        if int(level) != -777:
                            last_update = datetime.datetime.strptime(
                                values[0], '"%d.%m.%Y %H:%M"'
                            )
                            break
                    except:
                        continue
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
                    try:
                        flow = float(values[1].replace(",", "."))
                        if int(flow) != -777:
                            if last_update is None:
                                last_update = datetime.datetime.strptime(
                                    values[0], '"%d.%m.%Y %H:%M"'
                                )
                            break
                    except:
                        continue
        return DynamicData(level=level, flow=flow, last_update=last_update)
    except Exception as err:
        raise LHPError(err, "be_api.py: update_BE()") from err
