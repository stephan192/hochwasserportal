"""The Länderübergreifendes Hochwasser Portal API - Functions for Brandenburg."""

from __future__ import annotations
from collections import namedtuple
from .api_utils import LHPError, fetch_text
import datetime


def fix_bb_encoding(string_in):
    """Fix utf-8 encoding for BB"""
    replace = False
    cnt = 0
    string_out = ""
    for c in string_in:
        num = ord(c)
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
                if 47 < num < 58:
                    num = num - 48
                elif 64 < num < 71:
                    num = num - 55
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


def init_BB(ident):
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
            if start_found:
                if line == "}),":
                    break
                if line.count("'") == 2:
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
                        break
        Initdata = namedtuple("Initdata", ["name", "url"])
        return Initdata(name, url)
    except Exception as err:
        raise LHPError(err, "bb_api.py: init_BB()") from err


def update_BB(ident):
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
            if line == "pkz: '" + ident[3:] + "',":
                start_found = True
                stage_valid = bool(prev_line == "pegel: 'bbalarm',")
                continue
            if start_found:
                if line == "}),":
                    break
                if line.count("'") == 2:
                    key = line[: line.find(":")]
                    value = line.split("'")[1]
                if key == "alarmklasse":
                    # key is always available but content is not always valid
                    if stage_valid:
                        try:
                            stage = int(value)
                        except:
                            stage = None
                    else:
                        stage = None
                elif key == "datum":
                    timestamp = str(value)
                elif key == "zeit":
                    timestamp = timestamp + " " + str(value)
                    try:
                        last_update = datetime.datetime.strptime(
                            timestamp, "%d.%m.%Y %H:%M"
                        )
                    except:
                        last_update = None
                elif key == "wert":
                    try:
                        level = float(value.replace(",", "."))
                    except:
                        level = None
                elif key == "qwert":
                    try:
                        flow = float(value.replace(",", "."))
                    except:
                        flow = None
                    break
            prev_line = line
        Cyclicdata = namedtuple("Cyclicdata", ["level", "stage", "flow", "last_update"])
        return Cyclicdata(level, stage, flow, last_update)
    except Exception as err:
        raise LHPError(err, "bb_api.py: update_BB()") from err
