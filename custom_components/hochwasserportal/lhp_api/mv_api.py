"""The Länderübergreifendes Hochwasser Portal API - Functions for Mecklenburg-Vorpommern."""

from __future__ import annotations
from collections import namedtuple
from .api_utils import LHPError, fetch_soup
import datetime
import re


def init_MV(ident):
    """Init data for Mecklenburg-Vorpommern."""
    try:
        # Get data
        soup = fetch_soup("https://pegelportal-mv.de/pegel_list.html")
        table = soup.find("table", id="pegeltab")
        tbody = table.find("tbody")
        search_string = re.compile(ident[3:])
        link = tbody.find_next("a", href=search_string)
        tr = link.parent.parent
        tds = tr.find_all("td")
        # Parse data
        cnt = 0
        for td in tds:
            if cnt == 0:
                name = td.getText().strip()
            elif cnt == 1:
                name += " / " + td.getText().strip()
                break
            cnt += 1
        if ident.find(".") != -1:
            url = "https://pegelportal-mv.de/" + ident[3:] + ".html"
        else:
            url = link["href"]
        Initdata = namedtuple("Initdata", ["name", "url"])
        return Initdata(name, url)
    except Exception as err:
        raise LHPError(err, "mv_api.py: init_MV()") from err


def update_MV(ident):
    """Update data for Mecklenburg-Vorpommern."""
    try:
        # Get data
        soup = fetch_soup("https://pegelportal-mv.de/pegel_list.html")
        table = soup.find("table", id="pegeltab")
        tbody = table.find("tbody")
        search_string = re.compile(ident[3:])
        link = tbody.find_next("a", href=search_string)
        tr = link.parent.parent
        tds = tr.find_all("td")
        # Parse data
        cnt = 0
        for td in tds:
            if cnt == 2:
                try:
                    last_update = datetime.datetime.strptime(
                        td.getText().strip(), "%d.%m.%Y %H:%M"
                    )
                except:
                    last_update = None
            elif cnt == 3:
                try:
                    level = float(td.getText().strip())
                except:
                    level = None
            elif cnt == 4:
                try:
                    flow = float(td.getText().strip())
                except:
                    flow = None
                img = td.find_next("img")
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
        Cyclicdata = namedtuple("Cyclicdata", ["level", "stage", "flow", "last_update"])
        return Cyclicdata(level, stage, flow, last_update)
    except Exception as err:
        raise LHPError(err, "mv_api.py: update_MV()") from err
