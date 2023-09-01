"""The Länderübergreifendes Hochwasser Portal API - Functions for Baden-Württemberg."""

from __future__ import annotations

from datetime import datetime
from json import loads

from .api_utils import DynamicData, LHPError, StaticData, calc_stage, fetch_text


def init_BW(ident: str) -> StaticData:  # pylint: disable=invalid-name
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
            data = loads(content)["data"]
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


def update_BW(static_data: StaticData) -> DynamicData:  # pylint: disable=invalid-name
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
            data = loads(content)["data"]
            if data[0] == static_data.ident[3:]:
                try:
                    if data[5] == "cm":
                        level = float(data[4])
                        stage = calc_stage(level, static_data.stage_levels)
                        try:
                            parts = data[6].split()
                            last_update = datetime.strptime(
                                parts[0] + parts[1], "%d.%m.%Y%H:%M"
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
                        parts = data[9].split()
                        last_update = datetime.strptime(
                            parts[0] + parts[1], "%d.%m.%Y%H:%M"
                        )
                    except:
                        last_update = None
                break
        return DynamicData(level=level, stage=stage, flow=flow, last_update=last_update)
    except Exception as err:
        raise LHPError(err, "bw_api.py: update_BW()") from err
