"""The Länderübergreifendes Hochwasser Portal API - Functions for Bremen."""

from __future__ import annotations
from .api_utils import (
    LHPError,
    StaticData,
    DynamicData,
    fetch_json,
    fetch_text,
    calc_stage,
)
import datetime


def init_HB(ident: str) -> StaticData:
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
        if "station_name" in locals():
            prop_string = pb_page[pb_page.find("Stations:{") + 10 :].strip()
            prop_string = prop_string[prop_string.find("properties:[") + 12 :].strip()
            prop_string = prop_string[: prop_string.find(")]}")].strip()
            prop_string = prop_string[prop_string.find(station_name) - 1 :].strip()
            prop_string = prop_string[: prop_string.find(")")].strip()
            if prop_string.find("[") != -1:
                sl_string = prop_string[
                    prop_string.find("[") + 1 : prop_string.find("]")
                ]
                stage_levels = sl_string.split(",")
                stage_levels = [float(sl) for sl in stage_levels]
                while len(stage_levels) < 4:
                    stage_levels.append(None)
            return StaticData(
                ident=ident,
                name=name,
                internal_url=internal_url,
                url=url,
                stage_levels=stage_levels,
            )
        return StaticData(ident=ident)
    except Exception as err:
        raise LHPError(err, "hb_api.py: init_HB()") from err


def update_HB(static_data: StaticData) -> DynamicData:
    """Update data for Bremen."""
    try:
        # Get data
        data = fetch_json(static_data.internal_url)
        # Parse data
        if len(data) > 0:
            try:
                level = float(data[-1]["value"])
                stage = calc_stage(level, static_data.stage_levels)
            except:
                level = None
                stage = None
            try:
                last_update = datetime.datetime.fromisoformat(data[-1]["timestamp"])
            except:
                last_update = None
        return DynamicData(level=level, stage=stage, last_update=last_update)
    except Exception as err:
        raise LHPError(err, "hb_api.py: update_HB()") from err
