"""The Länderübergreifendes Hochwasser Portal API - Functions for Rheinland-Pfalz."""

from __future__ import annotations
from collections import namedtuple
from .api_utils import fetch_json, calc_stage
import datetime


def init_RP(ident):
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
                    stage_levels[0] = thresholds[key]["W"]["22"]
                    stage_levels[1] = thresholds[key]["W"]["21"]
                    stage_levels[2] = thresholds[key]["W"]["20"]
                    stage_levels[3] = thresholds[key]["W"]["19"]
                except:
                    stage_levels = [None] * 4
                dbg_msg = f"Stage levels : {stage_levels}"
                break
        Initdata = namedtuple("Initdata", ["name", "url", "stage_levels", "dbg_msg"])
        return Initdata(name, url, stage_levels, dbg_msg)
    except Exception as e:
        Initdata = namedtuple("Initdata", ["err_msg"])
        return Initdata(f"An error occured while fetching init data for {ident}: {e}")


def parse_RP(ident, stage_levels):
    """Parse data for Rheinland-Pfalz."""
    try:
        # Get data
        data = fetch_json(
            "https://hochwasser.rlp.de/api/v1/measurement-site/" + ident[3:]
        )
        # Parse data
        last_update_str = None
        try:
            level = float(data["W"]["yLast"])
            stage = calc_stage(level, stage_levels)
            last_update_str = data["W"]["xLast"][:-1] + "+00:00"
        except:
            level = None
            stage = None
        try:
            flow = float(data["Q"]["yLast"])
            if last_update_str is None:
                last_update_str = data["Q"]["xLast"][:-1] + "+00:00"
        except:
            flow = None
        if last_update_str is not None:
            last_update = datetime.datetime.fromisoformat(last_update_str)
        else:
            last_update = None
        Cyclicdata = namedtuple("Cyclicdata", ["level", "stage", "flow", "last_update"])
        return Cyclicdata(level, stage, flow, last_update)
    except Exception as e:
        Cyclicdata = namedtuple("Cyclicdata", ["err_msg"])
        return Cyclicdata(f"An error occured while fetching data for {ident}: {e}")
