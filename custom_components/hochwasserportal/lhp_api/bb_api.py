"""The Länderübergreifendes Hochwasser Portal API - Functions for Brandenburg."""

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


def substract_ascii_offset(num: int) -> int:
    """Substract ASCII offset."""
    if 47 < num < 58:
        return num - 48
    if 64 < num < 71:
        return num - 55
    return num


def fix_bb_encoding(string_in: str) -> str:
    """Fix utf-8 encoding for BB."""
    replace = False
    cnt = 0
    string_out = ""
    for char in string_in:
        num = ord(char)
        # Find '\'
        if num == 92:
            replace = True
            cnt = 0
            continue
        if replace:
            if cnt == 0:
                # Find '\u'
                if num == 117:
                    cnt += 1
                else:
                    string_out = string_out + chr(92)
                    string_out = string_out + chr(num)
                    replace = False
                    continue
            else:
                num = substract_ascii_offset(num)
                if cnt == 1:
                    new_num = num * 4096
                    cnt += 1
                elif cnt == 2:
                    new_num = new_num + (num * 256)
                    cnt += 1
                elif cnt == 3:
                    new_num = new_num + (num * 16)
                    cnt += 1
                elif cnt == 4:
                    new_num = new_num + num
                    string_out = string_out + chr(new_num)
                    replace = False
        else:
            string_out = string_out + chr(num)
    return string_out


def init_BB(ident: str) -> StaticData:  # pylint: disable=invalid-name
    """Init data for Brandenburg."""
    try:
        # Get data
        page = fetch_text("https://pegelportal.brandenburg.de/start.php")
        lines = page.split("\n")
        # Parse data
        start_found = False
        for line in lines:
            line = line.strip()
            if line == "pkz: '" + ident[3:] + "',":
                start_found = True
                continue
            if start_found and (line == "}),"):
                break
            if start_found and (line.count("'") == 2):
                key = line[: line.find(":")]
                value = line.split("'")[1]
                if key == "name":
                    name = fix_bb_encoding(str(value))
                elif key == "gewaesser":
                    name = name + " / " + fix_bb_encoding(str(value))
                elif key == "fgid":
                    url = (
                        "https://pegelportal.brandenburg.de/messstelle.php?fgid="
                        + str(value)
                        + "&pkz="
                        + ident[3:]
                    )
                    return StaticData(ident=ident, name=name, url=url)
        return StaticData(ident=ident)
    except Exception as err:
        raise LHPError(err, "bb_api.py: init_BB()") from err


def update_BB(static_data: StaticData) -> DynamicData:  # pylint: disable=invalid-name
    """Update data for Brandenburg."""
    try:
        # Get data
        page = fetch_text("https://pegelportal.brandenburg.de/start.php")
        lines = page.split("\n")
        # Parse data
        start_found = False
        prev_line = None
        for line in lines:
            line = line.strip()
            if line == "pkz: '" + static_data.ident[3:] + "',":
                start_found = True
                stage_valid = bool(prev_line == "pegel: 'bbalarm',")
                continue
            if start_found and (line == "}),"):
                break
            if start_found and (line.count("'") == 2):
                key = line[: line.find(":")]
                value = line.split("'")[1]
                if key == "alarmklasse":
                    # key is always available but content is not always valid
                    if stage_valid:
                        stage = convert_to_int(value)
                    else:
                        stage = None
                elif key == "datum":
                    timestamp = str(value)
                elif key == "zeit":
                    timestamp = timestamp + " " + str(value)
                    last_update = convert_to_datetime(timestamp, "%d.%m.%Y %H:%M")
                elif key == "wert":
                    level = convert_to_float(value, True)
                elif key == "qwert":
                    flow = convert_to_float(value, True)
                    return DynamicData(
                        level=level, stage=stage, flow=flow, last_update=last_update
                    )
            prev_line = line
        return DynamicData()
    except Exception as err:
        raise LHPError(err, "bb_api.py: update_BB()") from err
