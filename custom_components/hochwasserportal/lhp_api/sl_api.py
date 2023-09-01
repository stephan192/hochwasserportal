"""The Länderübergreifendes Hochwasser Portal API - Functions for Saarland."""

from __future__ import annotations
from .api_utils import LHPError, StaticData, DynamicData, fetch_text
import datetime


def init_SL(ident) -> StaticData:
    """Init data for Saarland."""
    try:
        # Get data
        page = fetch_text("https://iframe01.saarland.de/extern/wasser/Daten.js")
        lines = page.split("\r\n")
        # Parse data
        for line in lines:
            if (line.find("Pegel(") != -1) and (line.find(ident[3:]) != -1):
                content = line[line.find("Pegel(") + 6 : line.find(");")]
                content = content.replace("'", "")
                elements = content.split(",")
                if len(elements) == 9:
                    name = elements[4].strip() + " / " + elements[5].strip()
                    url = (
                        "https://iframe01.saarland.de/extern/wasser/L"
                        + ident[3:]
                        + ".htm"
                    )
                    break
        return StaticData(ident=ident, name=name, url=url)
    except Exception as err:
        raise LHPError(err, "sl_api.py: init_SL()") from err


def update_SL(ident) -> DynamicData:
    """Update data for Saarland."""
    try:
        # Get data
        page = fetch_text("https://iframe01.saarland.de/extern/wasser/Daten.js")
        lines = page.split("\r\n")
        # Parse data
        for line in lines:
            if (line.find("Pegel(") != -1) and (line.find(ident[3:]) != -1):
                content = line[line.find("Pegel(") + 6 : line.find(");")]
                content = content.replace("'", "")
                elements = content.split(",")
                if len(elements) == 9:
                    try:
                        # 1 = kein Hochwasser => stage = 0
                        # 2 = kleines Hochwasser => stage = 1
                        # 3 = mittleres Hochwasser => stage = 2
                        # 4 = großes Hochwasser => stage = 3
                        # 5 = Weiterer Pegel => stage = None
                        # 6 = Kein Kennwert => stage = None
                        # 7 = sehr großes Hochwasser => stage = 4
                        stage_int = int(elements[3].strip())
                        if stage_int == 7:
                            stage = 4
                        elif (stage_int > 0) and (stage_int < 5):
                            stage = stage_int - 1
                        else:
                            stage = None
                    except:
                        stage = None
                    try:
                        level = float(elements[6].strip())
                    except:
                        level = None
                    try:
                        last_update = datetime.datetime.strptime(
                            elements[7].strip() + "+0100", "%d.%m.%Y %H:%M%z"
                        )
                    except:
                        last_update = None
                    break
        return DynamicData(level=level, stage=stage, last_update=last_update)
    except Exception as err:
        raise LHPError(err, "sl_api.py: update_SL()") from err
