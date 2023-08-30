"""The Länderübergreifendes Hochwasser Portal API - Functions for Bremen."""

from __future__ import annotations
from collections import namedtuple
from .api_utils import fetch_json, fetch_text, calc_stage
import datetime


def init_HB(ident):
    """Init data for Bremen."""
    try:
        # Get data from Pegelstände Bremen
        pb_page = fetch_text(
            "https://geoportale.dp.dsecurecloud.de/pegelbremen/src.2c9c6cd7.js",
            forced_encoding="utf-8",
        )
        # Get data from PegelOnline
        pe_stations = fetch_json(
            "https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations.json"
        )
        # Parse data - Get list of stations
        stations_string = pb_page[pb_page.find("pegelonlineStations:[") + 21 :].strip()
        stations_string = stations_string[: stations_string.find("],")].strip()
        stations = stations_string.split(",")
        stations_names = [station.replace('"', "") for station in stations]
        stations_names_upper = [station.upper() for station in stations_names]
        # Parse data - Collect data from PegelOnlie
        for pe in pe_stations:
            if pe["number"] == ident[3:]:
                station_name = stations_names[
                    stations_names_upper.index(pe["longname"])
                ]
                name = station_name + " / " + pe["water"]["longname"].capitalize()
                internal_url = (
                    "https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations/"
                    + pe["uuid"]
                    + "/W/measurements.json?start=P1D"
                )
                url = (
                    "https://pegelonline.wsv.de/webservices/zeitreihe/visualisierung?pegeluuid="
                    + pe["uuid"]
                )
                break
        # Parse data - Collect stage levels from Pegelstände Bremen
        prop_string = pb_page[pb_page.find("Stations:{") + 10 :].strip()
        prop_string = prop_string[prop_string.find("properties:[") + 12 :].strip()
        prop_string = prop_string[: prop_string.find(")]}")].strip()
        prop_string = prop_string[prop_string.find(station_name) - 1 :].strip()
        prop_string = prop_string[: prop_string.find(")")].strip()
        if prop_string.find("[") != -1:
            sl_string = prop_string[prop_string.find("[") + 1 : prop_string.find("]")]
            stage_levels = sl_string.split(",")
            stage_levels = [float(sl) for sl in stage_levels]
            while len(stage_levels) < 4:
                stage_levels.append(None)
        Initdata = namedtuple(
            "Initdata", ["name", "url", "internal_url", "stage_levels"]
        )
        return Initdata(name, url, internal_url, stage_levels)
    except Exception as err_msg:
        Initdata = namedtuple("Initdata", ["err_msg"])
        return Initdata(err_msg)


def parse_HB(internal_url, stage_levels):
    """Parse data for Bremen."""
    try:
        # Get data
        data = fetch_json(internal_url)
        # Parse data
        if len(data) > 0:
            try:
                level = float(data[-1]["value"])
                stage = calc_stage(level, stage_levels)
            except:
                level = None
                stage = None
            try:
                last_update = datetime.datetime.fromisoformat(data[-1]["timestamp"])
            except:
                last_update = None
        Cyclicdata = namedtuple("Cyclicdata", ["level", "stage", "last_update"])
        return Cyclicdata(level, stage, last_update)
    except Exception as err_msg:
        Cyclicdata = namedtuple("Cyclicdata", ["err_msg"])
        return Cyclicdata(err_msg)
