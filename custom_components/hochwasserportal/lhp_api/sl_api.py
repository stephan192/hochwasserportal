"""The Länderübergreifendes Hochwasser Portal API - Functions for Saarland."""

from __future__ import annotations

from .api_utils import (
    DynamicData,
    LHPError,
    StaticData,
    convert_to_datetime,
    convert_to_float,
    convert_to_int,
    fetch_text,
)


def init_SL(ident: str) -> StaticData:  # pylint: disable=invalid-name
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
                    return StaticData(ident=ident, name=name, url=url)
        return StaticData(ident=ident)
    except Exception as err:
        raise LHPError(err, "sl_api.py: init_SL()") from err


def calc_sl_stage(value: str) -> int:
    """Calc stage for Saarland."""
    stage_int = convert_to_int(value)
    # 1 = kein Hochwasser => stage = 0
    # 2 = kleines Hochwasser => stage = 1
    # 3 = mittleres Hochwasser => stage = 2
    # 4 = großes Hochwasser => stage = 3
    # 5 = Weiterer Pegel => stage = None
    # 6 = Kein Kennwert => stage = None
    # 7 = sehr großes Hochwasser => stage = 4
    if stage_int == 7:
        return 4
    if 0 < stage_int < 5:
        return stage_int - 1
    return None


def update_SL(static_data: StaticData) -> DynamicData:  # pylint: disable=invalid-name
    """Update data for Saarland."""
    try:
        # Get data
        page = fetch_text("https://iframe01.saarland.de/extern/wasser/Daten.js")
        lines = page.split("\r\n")
        # Parse data
        for line in lines:
            if (line.find("Pegel(") != -1) and (line.find(static_data.ident[3:]) != -1):
                content = line[line.find("Pegel(") + 6 : line.find(");")]
                content = content.replace("'", "")
                elements = content.split(",")
                if len(elements) == 9:
                    stage = calc_sl_stage(elements[3].strip())
                    level = convert_to_float(elements[6].strip())
                    # Timestamps are always in CET/MEZ, ignoring daylight saving time
                    last_update = convert_to_datetime(
                        elements[7].strip() + "+0100", "%d.%m.%Y %H:%M%z"
                    )
                    return DynamicData(
                        level=level, stage=stage, last_update=last_update
                    )
        return DynamicData()
    except Exception as err:
        raise LHPError(err, "sl_api.py: update_SL()") from err
