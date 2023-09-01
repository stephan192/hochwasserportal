"""The Länderübergreifendes Hochwasser Portal API - Functions for Hessen."""

from __future__ import annotations
from .api_utils import LHPError, StaticData, DynamicData, fetch_json, calc_stage
import datetime


def init_HE(ident: str) -> StaticData:
    """Init data for Hessen."""
    try:
        name = None
        url = None
        internal_url = None
        hint = None
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
    except Exception as err:
        raise LHPError(err, "he_api.py: init_HE()") from err
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


def update_HE(static_data: StaticData) -> DynamicData:
    """Update data for Hessen."""
    last_update_str_w = None
    try:
        # Get data
        data = fetch_json(static_data.internal_url + "/W/week.json")
        # Parse data
        for dataset in data:
            if dataset["ts_name"] == "15.P":
                last_update_str_w = dataset["data"][-1][0]
                level = float(dataset["data"][-1][1])
                stage = calc_stage(level, static_data.stage_levels)
                break
    except:
        level = None
        stage = None

    last_update_str_q = None
    try:
        # Get data
        data = fetch_json(static_data.internal_url + "/Q/week.json")
        # Parse data
        for dataset in data:
            if dataset["ts_name"] == "15.P":
                last_update_str_q = dataset["data"][-1][0]
                flow = float(dataset["data"][-1][1])
                break
    except:
        flow = None

    last_update = None
    if level is not None:
        last_update = datetime.datetime.fromisoformat(last_update_str_w)
    elif flow is not None:
        last_update = datetime.datetime.fromisoformat(last_update_str_q)
    if last_update is not None:
        return DynamicData(level=level, stage=stage, flow=flow, last_update=last_update)
    raise LHPError("An error occured while fetching data!", "he_api.py: update_HE()")
