"""The Länderübergreifendes Hochwasser Portal API - Functions for Bremen."""

from __future__ import annotations

from .api_utils import (
    DynamicData,
    LHPError,
    StaticData,
    calc_stage,
    convert_to_datetime,
    convert_to_float,
    fetch_json,
    fetch_text,
)


def get_basic_station_data(
    ident: str, stations_names: list[str]
) -> tuple[str, str, str, str]:
    """Get basic station data."""
    # Get data from PegelOnline
    pe_stations = fetch_json(
        "https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations.json"
    )
    stations_names_upper = [station.upper() for station in stations_names]
    # Parse data
    station_name = None
    name = None
    internal_url = None
    url = None
    for pe_st in pe_stations:
        if pe_st["number"] == ident[3:]:
            station_name = stations_names[stations_names_upper.index(pe_st["longname"])]
            name = station_name + " / " + pe_st["water"]["longname"].capitalize()
            internal_url = (
                "https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations/"
                + pe_st["uuid"]
                + "/W/measurements.json?start=P1D"
            )
            url = (
                "https://pegelonline.wsv.de/webservices/zeitreihe/visualisierung?pegeluuid="
                + pe_st["uuid"]
            )
            break
    return (station_name, name, internal_url, url)


def get_stage_levels(pb_page: str, station_name: str) -> list[float]:
    """Get stage levels."""
    stage_levels = [None] * 4
    prop_string = pb_page[pb_page.find("Stations:{") + 10 :].strip()
    prop_string = prop_string[prop_string.find("properties:[") + 12 :].strip()
    prop_string = prop_string[: prop_string.find(")]}")].strip()
    prop_string = prop_string[prop_string.find(station_name) - 1 :].strip()
    prop_string = prop_string[: prop_string.find(")")].strip()
    if prop_string.find("[") != -1:
        sl_string = prop_string[prop_string.find("[") + 1 : prop_string.find("]")]
        stage_levels = sl_string.split(",")
        stage_levels = [convert_to_float(sl) for sl in stage_levels]
        while len(stage_levels) < 4:
            stage_levels.append(None)
    return stage_levels


def init_HB(ident: str) -> StaticData:  # pylint: disable=invalid-name
    """Init data for Bremen."""
    try:
        # Get script url
        pb_page = fetch_text(
            "https://geoportale.dp.dsecurecloud.de/pegelbremen", forced_encoding="utf-8"
        )
        js_file = pb_page[pb_page.find('<script src="') + 13 :].strip()
        js_file = js_file[: js_file.find('"></script>')].strip()
        js_url = "https://geoportale.dp.dsecurecloud.de/pegelbremen/" + js_file
        # Get data from Pegelstände Bremen
        pb_page = fetch_text(js_url, forced_encoding="utf-8")
        # Parse data - Get list of stations
        stations_string = pb_page[pb_page.find("pegelonlineStations:[") + 21 :].strip()
        stations_string = stations_string[: stations_string.find("],")].strip()
        stations = stations_string.split(",")
        stations_names = [station.replace('"', "") for station in stations]
        # Parse data - Collect data from PegelOnline
        (station_name, name, internal_url, url) = get_basic_station_data(
            ident, stations_names
        )
        # Parse data - Collect stage levels from Pegelstände Bremen
        if station_name is not None:
            stage_levels = get_stage_levels(pb_page, station_name)
        else:
            stage_levels = [None] * 4
        return StaticData(
            ident=ident,
            name=name,
            internal_url=internal_url,
            url=url,
            stage_levels=stage_levels,
        )
    except Exception as err:
        raise LHPError(err, "hb_api.py: init_HB()") from err


def update_HB(static_data: StaticData) -> DynamicData:  # pylint: disable=invalid-name
    """Update data for Bremen."""
    try:
        # Get data
        data = fetch_json(static_data.internal_url)
        # Parse data
        if len(data) > 0:
            level = convert_to_float(data[-1]["value"])
            stage = calc_stage(level, static_data.stage_levels)
            last_update = convert_to_datetime(data[-1]["timestamp"], "iso")
            return DynamicData(level=level, stage=stage, last_update=last_update)
        return DynamicData()
    except Exception as err:
        raise LHPError(err, "hb_api.py: update_HB()") from err
