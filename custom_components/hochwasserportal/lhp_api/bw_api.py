"""The Länderübergreifendes Hochwasser Portal API - Functions for Baden-Württemberg."""

from __future__ import annotations
from .api_utils import LHPError, StaticData, DynamicData, fetch_text, calc_stage
import datetime
import json


def init_BW(ident) -> StaticData:
    """Init data for Baden-Württemberg."""
    try:
        # Get data
        page = fetch_text("https://www.hvz.baden-wuerttemberg.de/js/hvz_peg_stmn.js")
        lines = page.split("\r\n")[6:-4]
        # Parse data
        stage_levels = [None] * 4
        for line in lines:
            # Building a valid json string
            content = line[line.find("[") : (line.find("]") + 1)]
            content = content.replace("'", '"')
            content = '{ "data":' + content + "}"
            data = json.loads(content)["data"]
            if data[0] == ident[3:]:
                name = data[1] + " / " + data[2]
                url = "https://hvz.baden-wuerttemberg.de/pegel.html?id=" + ident[3:]
                if float(data[24]) > 0.0:
                    stage_levels[0] = round(float(data[24]) * 100.0, 0)
                if data[30] > 0:
                    if (stage_levels[0] is None) or (float(data[30]) < stage_levels[0]):
                        stage_levels[0] = float(data[30])
                if data[31] > 0:
                    stage_levels[1] = float(data[31])
                if data[32] > 0:
                    stage_levels[2] = float(data[32])
                if data[33] > 0:
                    stage_levels[3] = float(data[33])
                break
        return StaticData(ident=ident, name=name, url=url, stage_levels=stage_levels)
    except Exception as err:
        raise LHPError(err, "bw_api.py: init_BW()") from err


def update_BW(ident, stage_levels) -> DynamicData:
    """Update data for Baden-Württemberg."""
    try:
        # Get data
        page = fetch_text("https://www.hvz.baden-wuerttemberg.de/js/hvz_peg_stmn.js")
        lines = page.split("\r\n")[6:-4]
        # Parse data
        last_update = None
        for line in lines:
            # Building a valid json string
            content = line[line.find("[") : (line.find("]") + 1)]
            content = content.replace("'", '"')
            content = '{ "data":' + content + "}"
            data = json.loads(content)["data"]
            if data[0] == ident[3:]:
                try:
                    if data[5] == "cm":
                        level = float(data[4])
                        stage = calc_stage(level, stage_levels)
                        try:
                            dt = data[6].split()
                            last_update = datetime.datetime.strptime(
                                dt[0] + dt[1], "%d.%m.%Y%H:%M"
                            )
                        except:
                            last_update = None
                    else:
                        level = None
                        stage = None
                except:
                    level = None
                    stage = None
                try:
                    if data[8] == "m³/s":
                        flow = float(data[7])
                    else:
                        flow = None
                except:
                    flow = None
                if last_update is None:
                    try:
                        dt = data[9].split()
                        last_update = datetime.datetime.strptime(
                            dt[0] + dt[1], "%d.%m.%Y%H:%M"
                        )
                    except:
                        last_update = None
                break
        return DynamicData(level=level, stage=stage, flow=flow, last_update=last_update)
    except Exception as err:
        raise LHPError(err, "bw_api.py: update_BW()") from err
