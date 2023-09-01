"""The Länderübergreifendes Hochwasser Portal API - Functions for Sachsen-Anhalt."""

from __future__ import annotations
from .api_utils import LHPError, StaticData, DynamicData, fetch_json, calc_stage
import datetime


def init_ST(ident) -> StaticData:
    """Init data for Sachsen-Anhalt."""
    try:
        name = None
        url = None
        internal_url = None
        hint = None
        # Get Stations Data
        st_stations = fetch_json(
            "https://hvz.lsaurl.de/fileadmin/Bibliothek/Politik_und_Verwaltung/MLU/HVZ/KISTERS/data/internet/stations/stations.json"
        )
        for station in st_stations:
            if station["station_no"] == ident[3:]:
                name = (
                    station["station_name"].strip()
                    + " / "
                    + station["WTO_OBJECT"].strip()
                )
                url = "https://hvz.lsaurl.de/#" + ident[3:]
                internal_url = (
                    "https://hvz.lsaurl.de/fileadmin/Bibliothek/Politik_und_Verwaltung/MLU/HVZ/KISTERS/data/internet/stations/"
                    + station["site_no"]
                    + "/"
                    + ident[3:]
                )
                hint = (
                    station["web_anmerkung"].strip()
                    + " "
                    + station["web_wichtigerhinweis"].strip()
                ).strip()
                if len(hint) == 0:
                    hint = None
                break
    except Exception as err:
        raise LHPError(err, "st_api.py: init_ST()") from err
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
                    if station_data["ts_name"] == "Alarmstufe 1":
                        stage_levels[0] = float(station_data["data"][-1][1])
                    elif station_data["ts_name"] == "Alarmstufe 2":
                        stage_levels[1] = float(station_data["data"][-1][1])
                    elif station_data["ts_name"] == "Alarmstufe 3":
                        stage_levels[2] = float(station_data["data"][-1][1])
                    elif station_data["ts_name"] == "Alarmstufe 4":
                        stage_levels[3] = float(station_data["data"][-1][1])
    except:
        stage_levels = [None] * 4
    return StaticData(
        ident=ident,
        name=name,
        internal_url=internal_url,
        url=url,
        hint=hint,
        stage_levels=stage_levels,
    )


def update_ST(internal_url, stage_levels) -> DynamicData:
    """Update data for Sachsen-Anhalt."""
    last_update_str_w = None
    try:
        # Get data
        data = fetch_json(internal_url + "/W/week.json")
        # Parse data
        last_update_str_w = data[0]["data"][-1][0]
        level = float(data[0]["data"][-1][1])
        stage = calc_stage(level, stage_levels)
    except:
        level = None
        stage = None

    last_update_str_q = None
    try:
        # Get data
        data = fetch_json(internal_url + "/Q/week.json")
        # Parse data
        last_update_str_q = data[0]["data"][-1][0]
        flow = float(data[0]["data"][-1][1])
    except:
        flow = None

    last_update = None
    if level is not None:
        last_update = datetime.datetime.fromisoformat(last_update_str_w)
    elif flow is not None:
        last_update = datetime.datetime.fromisoformat(last_update_str_q)
    if last_update is not None:
        return DynamicData(level=level, stage=stage, flow=flow, last_update=last_update)
    raise LHPError("An error occured while fetching data!", "st_api.py: update_ST()")
