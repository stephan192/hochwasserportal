"""The Länderübergreifendes Hochwasser Portal API - Functions for Rheinland-Pfalz."""

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


def init_RP(ident: str) -> StaticData:  # pylint: disable=invalid-name
    """Init data for Rheinland-Pfalz."""
    try:
        # Get data
        data = fetch_json("https://hochwasser.rlp.de/api/v1/config")
        measurementsites = data["measurementsite"]
        rivers = data["rivers"]
        riverareas = data["riverareas"]
        thresholds = data["legends"]["thresholds"]
        # Parse data
        for key in measurementsites:
            site = measurementsites[key]
            if site["number"] == ident[3:]:
                name = site["name"] + " / " + rivers[site["rivers"][0]]["name"]
                url = (
                    "https://www.hochwasser.rlp.de/flussgebiet/"
                    + riverareas[str(site["riverAreas"][0])]["name"].lower()
                    + "/"
                    + site["name"]
                    .replace(" ", "-")
                    .replace(",", "")
                    .replace("ß", "ss")
                    .replace("ä", "ae")
                    .replace("ö", "oe")
                    .replace("ü", "ue")
                    .lower()
                )
                try:
                    stage_levels = [None] * 4
                    stage_levels[0] = convert_to_float(thresholds[key]["W"]["22"])
                    stage_levels[1] = convert_to_float(thresholds[key]["W"]["21"])
                    stage_levels[2] = convert_to_float(thresholds[key]["W"]["20"])
                    stage_levels[3] = convert_to_float(thresholds[key]["W"]["19"])
                except (IndexError, KeyError):
                    stage_levels = [None] * 4
                return StaticData(
                    ident=ident, name=name, url=url, stage_levels=stage_levels
                )
        return StaticData(ident=ident)
    except Exception as err:
        raise LHPError(err, "rp_api.py: init_RP()") from err


def update_RP(static_data: StaticData) -> DynamicData:  # pylint: disable=invalid-name
    """Update data for Rheinland-Pfalz."""
    try:
        # Get data
        data = fetch_json(
            "https://hochwasser.rlp.de/api/v1/measurement-site/" + static_data.ident[3:]
        )
        # Parse data
        last_update_str = None
        try:
            level = convert_to_float(data["W"]["yLast"])
            stage = calc_stage(level, static_data.stage_levels)
            last_update_str = data["W"]["xLast"][:-1] + "+00:00"
        except (IndexError, KeyError):
            level = None
            stage = None
        try:
            flow = convert_to_float(data["Q"]["yLast"])
            if last_update_str is None:
                last_update_str = data["Q"]["xLast"][:-1] + "+00:00"
        except (IndexError, KeyError):
            flow = None
        if last_update_str is not None:
            last_update = convert_to_datetime(last_update_str, "iso")
        else:
            last_update = None
        return DynamicData(level=level, stage=stage, flow=flow, last_update=last_update)
    except Exception as err:
        raise LHPError(err, "rp_api.py: update_RP()") from err
