"""The Länderübergreifendes Hochwasser Portal API - Functions for Thüringen."""

from __future__ import annotations
from collections import namedtuple
from .api_utils import fetch_soup
import datetime


def init_TH(ident):
    """Init data for Thüringen."""
    try:
        # Get data
        soup = fetch_soup("https://hnz.thueringen.de/hw-portal/thueringen.html")
        table = soup.find_all("table", id="pegelTabelle")[0]
        tbody = table.find_all("tbody")[0]
        trs = tbody.find_all("tr")
        # Parse data
        for tr in trs:
            tds = tr.find_all("td")
            cnt = 0
            for td in tds:
                if (cnt == 1) and (td.getText().strip() != ident[3:]):
                    break
                if cnt == 1:
                    links = td.find_all("a")
                    url = "https://hnz.thueringen.de" + links[0]["href"]
                elif cnt == 2:
                    name = td.getText().strip()
                elif cnt == 3:
                    name += " / " + td.getText().strip()
                    break
                cnt += 1
            if cnt == 3:
                break
        Initdata = namedtuple("Initdata", ["name", "url"])
        return Initdata(name, url)
    except Exception as err_msg:
        Initdata = namedtuple("Initdata", ["err_msg"])
        return Initdata(err_msg)


def parse_TH(ident):
    """Parse data for Thüringen."""
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
        for tr in trs:
            tds = tr.find_all("td")
            cnt = 0
            for td in tds:
                if (cnt == 1) and (td.getText().strip() != ident[3:]):
                    break
                if cnt == 7:
                    last_update_str = td.getText().strip()
                elif cnt == 8:
                    level = float(td.getText().strip().replace(",", "."))
                elif cnt == 10:
                    flow = float(td.getText().strip().replace(",", "."))
                    break
                cnt += 1
            if cnt == 10:
                break
        if last_update_str is not None:
            last_update = datetime.datetime.strptime(last_update_str, "%d.%m.%Y %H:%M")
        else:
            last_update = None
        Cyclicdata = namedtuple("Cyclicdata", ["level", "flow", "last_update"])
        return Cyclicdata(level, flow, last_update)
    except Exception as err_msg:
        Cyclicdata = namedtuple("Cyclicdata", ["err_msg"])
        return Cyclicdata(err_msg)
