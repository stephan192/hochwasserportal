"""The Länderübergreifendes Hochwasser Portal API - Functions for Nordrhein-Westfalen."""

from __future__ import annotations

from datetime import datetime

from .api_utils import DynamicData, LHPError, StaticData, calc_stage, fetch_json


def init_NW(ident: str) -> StaticData:  # pylint: disable=invalid-name
    """Init data for Nordrhein-Westfalen."""
    try:
        # Get stations data
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
        # Get stage levels and hint
        stage_levels = [None] * 4
        if internal_url is not None:
            # Get stage levels
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
                        stage_levels[0] = float(station_data["data"][-1][1])
                    elif station_data["ts_name"] == "W.Informationswert_2":
                        stage_levels[1] = float(station_data["data"][-1][1])
                    elif station_data["ts_name"] == "W.Informationswert_3":
                        stage_levels[2] = float(station_data["data"][-1][1])
            # Get hint
            data = fetch_json(internal_url + "/S/week.json")
            hint = None
            if len(data[0]["AdminStatus"].strip()) > 0:
                hint = data[0]["AdminStatus"].strip()
            if len(data[0]["AdminBemerkung"].strip()) > 0:
                if len(hint) > 0:
                    hint += " / " + data[0]["AdminBemerkung"].strip()
                else:
                    hint = data[0]["AdminBemerkung"].strip()
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
            level = float(data[0]["data"][-1][1])
            stage = calc_stage(level, static_data.stage_levels)
            # Extract the last update timestamp from the JSON data
            last_update_str = data[0]["data"][-1][0]
            # Convert the string timestamp to a datetime object
            last_update = datetime.fromisoformat(last_update_str)
        else:
            level = None
            stage = None
            last_update = None
        return DynamicData(level=level, stage=stage, last_update=last_update)
    except Exception as err:
        raise LHPError(err, "nw_api.py: update_NW()") from err
