"""The Länderübergreifendes Hochwasser Portal API - Functions for Sachsen-Anhalt."""

from __future__ import annotations

import requests

from .api_utils import (
    DynamicData,
    LHPError,
    StaticData,
    calc_stage,
    convert_to_datetime,
    convert_to_float,
    fetch_json,
)


def get_basic_station_data(ident: str) -> tuple[str, str, str, str]:
    """Get basic station data."""
    name = None
    internal_url = None
    url = None
    hint = None
    st_stations = fetch_json(
        "https://hvz.lsaurl.de/fileadmin/Bibliothek/Politik_und_Verwaltung"
        + "/MLU/HVZ/KISTERS/data/internet/stations/stations.json"
    )
    for station in st_stations:
        if station["station_no"] == ident[3:]:
            name = (
                station["station_name"].strip() + " / " + station["WTO_OBJECT"].strip()
            )
            url = "https://hvz.lsaurl.de/#" + ident[3:]
            internal_url = (
                "https://hvz.lsaurl.de/fileadmin/Bibliothek/Politik_und_Verwaltung"
                + "/MLU/HVZ/KISTERS/data/internet/stations/"
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
    return (name, internal_url, url, hint)


def get_stage_levels(internal_url: str) -> list[float]:
    """Get stage levels."""
    stage_levels = [None] * 4
    try:
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
                    stage_levels[0] = convert_to_float(station_data["data"][-1][1])
                elif station_data["ts_name"] == "Alarmstufe 2":
                    stage_levels[1] = convert_to_float(station_data["data"][-1][1])
                elif station_data["ts_name"] == "Alarmstufe 3":
                    stage_levels[2] = convert_to_float(station_data["data"][-1][1])
                elif station_data["ts_name"] == "Alarmstufe 4":
                    stage_levels[3] = convert_to_float(station_data["data"][-1][1])
    # eg, 502180/W/alarmlevel.json does not exist (404)
    except requests.exceptions.HTTPError:
        pass
    return stage_levels


def init_ST(ident: str) -> StaticData:  # pylint: disable=invalid-name
    """Init data for Sachsen-Anhalt."""
    try:
        # Get Stations Data
        (name, internal_url, url, hint) = get_basic_station_data(ident)
        if internal_url is not None:
            stage_levels = get_stage_levels(internal_url)
        else:
            stage_levels = [None] * 4
        return StaticData(
            ident=ident,
            name=name,
            internal_url=internal_url,
            url=url,
            hint=hint,
            stage_levels=stage_levels,
        )
    except Exception as err:
        raise LHPError(err, "st_api.py: init_ST()") from err


def update_ST(static_data: StaticData) -> DynamicData:  # pylint: disable=invalid-name
    """Update data for Sachsen-Anhalt."""
    try:
        last_update_str_w = None
        try:
            # Get data
            data = fetch_json(static_data.internal_url + "/W/week.json")
            # Parse data
            last_update_str_w = data[0]["data"][-1][0]
            level = convert_to_float(data[0]["data"][-1][1])
            stage = calc_stage(level, static_data.stage_levels)
        # requests.exceptions.HTTPError for handling 404 etc
        except (IndexError, KeyError, requests.exceptions.HTTPError):
            level = None
            stage = None

        last_update_str_q = None
        try:
            # Get data
            data = fetch_json(static_data.internal_url + "/Q/week.json")
            # Parse data
            last_update_str_q = data[0]["data"][-1][0]
            flow = convert_to_float(data[0]["data"][-1][1])
        # requests.exceptions.HTTPError for handling 404 etc
        except (IndexError, KeyError, requests.exceptions.HTTPError):
            flow = None

        last_update = None
        if level is not None:
            last_update = convert_to_datetime(last_update_str_w, "iso")
        elif flow is not None:
            last_update = convert_to_datetime(last_update_str_q, "iso")
        return DynamicData(level=level, stage=stage, flow=flow, last_update=last_update)
    except Exception as err:
        raise LHPError(err, "st_api.py: update_ST()") from err
