"""The Länderübergreifendes Hochwasser Portal API - Functions for Hessen."""

from __future__ import annotations
from collections import namedtuple
from .api_utils import fetch_json, calc_stage
import datetime


def init_HE(ident):
    """Init data for Hessen."""
    try:
        # Get Stations Data
        he_stations = fetch_json(
            "https://www.hlnug.de/static/pegel/wiskiweb3/data/internet/stations/stations.json"
        )
        for station in he_stations:
            if station["station_no"] == ident[3:]:
                name = (
                    station["station_name"].strip()
                    + " / "
                    + station["WTO_OBJECT"].strip()
                )
                url = (
                    "https://www.hlnug.de/static/pegel/wiskiweb3/webpublic/#/overview/Wasserstand/station/"
                    + station["station_id"]
                    + "/"
                    + station["station_name"]
                    + "/Wasserstand"
                )
                internal_url = (
                    "https://www.hlnug.de/static/pegel/wiskiweb3/data/internet/stations/"
                    + station["site_no"]
                    + "/"
                    + station["station_no"]
                )
                hint = station["INTERNET_BEMERKUNG"].strip()
                if len(hint) == 0:
                    hint = None
                break
    except Exception as e:
        Initdata = namedtuple("Initdata", ["err_msg"])
        return Initdata(f"An error occured while fetching init data for {ident}: {e}")
    try:
        # Get stage levels
        stage_levels = [None] * 4
        if internal_url is not None:
            alarmlevels = fetch_json(internal_url + "/W/alarmlevel.json")
            for station_data in alarmlevels:
                if (
                    "ts_name" in station_data
                    and "data" in station_data
                    and isinstance(station_data["data"], list)
                    and len(station_data["data"]) > 0
                ):
                    # Check if ts_name is one of the desired values
                    if station_data["ts_name"] == "Meldestufe1":
                        stage_levels[0] = float(station_data["data"][-1][1])
                    elif station_data["ts_name"] == "Meldestufe2":
                        stage_levels[1] = float(station_data["data"][-1][1])
                    # No equivalent to stage_levels[2] available
                    elif station_data["ts_name"] == "Meldestufe3":
                        stage_levels[3] = float(station_data["data"][-1][1])
            dbg_msg = f"Stage levels : {stage_levels}"
    except:
        stage_levels = [None] * 4
        dbg_msg = f"{ident}: No stage levels available"
    Initdata = namedtuple(
        "Initdata", ["name", "url", "internal_url", "hint", "stage_levels", "dbg_msg"]
    )
    return Initdata(name, url, internal_url, hint, stage_levels, dbg_msg)


def parse_HE(ident, internal_url, stage_levels):
    """Parse data for Hessen."""
    if internal_url is None:
        Cyclicdata = namedtuple("Cyclicdata", ["err_msg"])
        return Cyclicdata(f"Internal url not set for {ident}")

    dbg_msg = None
    last_update_str_w = None
    try:
        # Get data
        data = fetch_json(internal_url + "/W/week.json")
        # Parse data
        for dataset in data:
            if dataset["ts_name"] == "15.P":
                last_update_str_w = dataset["data"][-1][0]
                level = float(dataset["data"][-1][1])
                stage = calc_stage(level, stage_levels)
                break
    except:
        level = None
        stage = None
        dbg_msg = f"{ident}: No level data available"

    last_update_str_q = None
    try:
        # Get data
        data = fetch_json(internal_url + "/Q/week.json")
        # Parse data
        for dataset in data:
            if dataset["ts_name"] == "15.P":
                last_update_str_q = dataset["data"][-1][0]
                flow = float(dataset["data"][-1][1])
                break
    except:
        flow = None
        if dbg_msg is None:
            dbg_msg = f"{ident}: No flow data available"
        else:
            dbg_msg = dbg_msg + ", No flow data available"

    if level is not None:
        last_update = datetime.datetime.fromisoformat(last_update_str_w)
    elif flow is not None:
        last_update = datetime.datetime.fromisoformat(last_update_str_q)
    if last_update is not None:
        Cyclicdata = namedtuple("Cyclicdata", ["level", "stage", "flow", "last_update"])
        return Cyclicdata(level, stage, flow, last_update)
    Cyclicdata = namedtuple("Cyclicdata", ["err_msg"])
    return Cyclicdata(f"An error occured while fetching data for {ident}")
