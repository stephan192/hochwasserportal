"""The Länderübergreifendes Hochwasser Portal API - Functions for Nordrhein-Westfalen."""

from __future__ import annotations

from .api_utils import (
    DynamicData,
    LHPError,
    StaticData,
    calc_stage,
    convert_to_datetime,
    convert_to_float,
    fetch_json,
)


def get_basic_station_data(ident: str) -> tuple[str, str, str]:
    """Get basic station data."""
    name = None
    internal_url = None
    url = None
    nw_stations = fetch_json(
        "https://hochwasserportal.nrw/lanuv/data/internet/stations/stations.json"
    )
    for station in nw_stations:
        if station["station_no"] == ident[3:]:
            name = station["station_name"] + " / " + station["WTO_OBJECT"]
            internal_url = (
                "https://hochwasserportal.nrw/lanuv/data/internet/stations/"
                + station["site_no"]
                + "/"
                + station["station_no"]
            )
            url = (
                "https://hochwasserportal.nrw/lanuv/webpublic/index.html#"
                + "/overview/Wasserstand/station/"
                + station["station_id"]
                + "/"
                + station["station_name"]
            )
            break
    return (name, internal_url, url)


def get_stage_levels(internal_url: str) -> list[float]:
    """Get stage levels."""
    stage_levels = [None] * 4
    nw_stages = fetch_json(internal_url + "/S/alarmlevel.json")
    for station_data in nw_stages:
        # Unfortunately the source data seems quite incomplete.
        # So we check if the required keys are present in the station_data dictionary:
        if (
            "ts_name" in station_data
            and "data" in station_data
            and isinstance(station_data["data"], list)
            and len(station_data["data"]) > 0
        ):
            # Check if ts_name is one of the desired values
            if station_data["ts_name"] == "W.Informationswert_1":
                stage_levels[0] = convert_to_float(station_data["data"][-1][1])
            elif station_data["ts_name"] == "W.Informationswert_2":
                stage_levels[1] = convert_to_float(station_data["data"][-1][1])
            elif station_data["ts_name"] == "W.Informationswert_3":
                stage_levels[2] = convert_to_float(station_data["data"][-1][1])
    return stage_levels


def get_hint(internal_url: str) -> str:
    """Get hint."""
    hint = None
    data = fetch_json(internal_url + "/S/week.json")
    if len(data[0]["AdminStatus"].strip()) > 0:
        hint = data[0]["AdminStatus"].strip()
    if len(data[0]["AdminBemerkung"].strip()) > 0:
        if len(hint) > 0:
            hint += " / " + data[0]["AdminBemerkung"].strip()
        else:
            hint = data[0]["AdminBemerkung"].strip()
    return hint


def init_NW(ident: str) -> StaticData:  # pylint: disable=invalid-name
    """Init data for Nordrhein-Westfalen."""
    try:
        # Get stations data
        (name, internal_url, url) = get_basic_station_data(ident)
        # Get stage levels and hint
        if internal_url is not None:
            stage_levels = get_stage_levels(internal_url)
            hint = get_hint(internal_url)
        else:
            stage_levels = [None] * 4
            hint = None
        return StaticData(
            ident=ident,
            name=name,
            internal_url=internal_url,
            url=url,
            hint=hint,
            stage_levels=stage_levels,
        )
    except Exception as err:
        raise LHPError(err, "nw_api.py: init_NW()") from err


def update_NW(static_data: StaticData) -> DynamicData:  # pylint: disable=invalid-name
    """Update data for Nordrhein-Westfalen."""
    try:
        # Get data
        data = fetch_json(static_data.internal_url + "/S/week.json")
        # Parse data
        if (
            "data" in data[0]
            and isinstance(data[0]["data"], list)
            and len(data[0]["data"]) > 0
        ):
            level = convert_to_float(data[0]["data"][-1][1])
            stage = calc_stage(level, static_data.stage_levels)
            last_update = convert_to_datetime(data[0]["data"][-1][0], "iso")
        else:
            level = None
            stage = None
            last_update = None
        return DynamicData(level=level, stage=stage, last_update=last_update)
    except Exception as err:
        raise LHPError(err, "nw_api.py: update_NW()") from err
