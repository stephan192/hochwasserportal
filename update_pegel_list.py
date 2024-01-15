"""The Länderübergreifendes Hochwasser Portal API - Utility module to update pegel.md."""

from __future__ import annotations

import json
import re
from typing import Any

from bs4 import BeautifulSoup
from requests import get


def fetch_json(url: str, timeout: float = 10.0) -> Any:
    """Fetch data via json."""
    response = get(url=url, timeout=timeout)
    response.raise_for_status()
    json_data = response.json()
    return json_data


def fetch_soup(
    url: str, timeout: float = 10.0, remove_xml: bool = False
) -> BeautifulSoup:
    """Fetch data via soup."""
    response = get(url=url, timeout=timeout)
    # Override encoding by real educated guess (required for e.g. SH)
    response.encoding = response.apparent_encoding
    response.raise_for_status()
    if remove_xml and (
        (response.text.find('<?xml version="1.0" encoding="ISO-8859-15" ?>')) == 0
    ):
        text = response.text[response.text.find("<!DOCTYPE html>") :]
        soup = BeautifulSoup(text, "lxml")
    else:
        soup = BeautifulSoup(response.text, "lxml")
    return soup


def fetch_text(url: str, timeout: float = 10.0, forced_encoding: str = None) -> str:
    """Fetch data via text."""
    response = get(url=url, timeout=timeout)
    if forced_encoding is not None:
        response.encoding = forced_encoding
    else:
        # Override encoding by real educated guess (required for e.g. BW)
        response.encoding = response.apparent_encoding
    response.raise_for_status()
    return response.text


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


def get_bb_stations() -> tuple[str, str]:
    """Get all available stations for Brandenburg."""
    stations = []
    page = fetch_text("https://pegelportal.brandenburg.de/start.php")
    lines = page.split("\n")
    start_found = False
    for line in lines:
        line = line.strip()
        if line in [
            "var layer_bb_alarm_ws = new ol.layer.Vector({",
            "var layer_bb_ws = new ol.layer.Vector({",
        ]:
            start_found = True
            continue
        if start_found:
            if line == "})":
                start_found = False
            if line.count("'") == 2:
                key = line[: line.find(":")]
                value = line.split("'")[1]
                if key == "pkz":
                    ident = "BB_" + str(value)
                elif key == "name":
                    name = fix_bb_encoding(str(value))
                elif key == "gewaesser":
                    name = name + " / " + fix_bb_encoding(str(value))
                    stations.append((ident, name))
    return stations


def get_be_stations() -> tuple[str, str]:
    """Get all available stations for Berlin."""
    stations = []
    page = fetch_soup(
        "https://wasserportal.berlin.de/start.php?anzeige=tabelle_ow&messanzeige=ms_ow_berlin",
        remove_xml=True,
    )
    table = page.find("table", id="pegeltab")
    tbody = table.find("tbody")
    trs = tbody.find_all("tr")
    for row in trs:
        tds = row.find_all("td")
        if len(tds) == 10:
            if (tds[3].getText().find("Wasserstand") != -1) and (
                tds[0].find_next("a")["href"][:12] == "station.php?"
            ):
                ident = "BE_" + tds[0].getText().strip()
                name = tds[1].getText().strip() + " / " + tds[4].getText().strip()
                stations.append((ident, name))
    return stations


def get_bw_stations() -> tuple[str, str]:
    """Get all available stations for Baden-Württemberg."""
    stations = []
    page = fetch_text("https://www.hvz.baden-wuerttemberg.de/js/hvz_peg_stmn.js")
    lines = page.split("\r\n")[6:-4]
    for line in lines:
        content = line[line.find("[") : line.find("]") + 1]
        content = content.replace("'", '"')
        content = '{ "data":' + content + "}"
        data = json.loads(content)["data"]
        ident = "BW_" + data[0]
        name = data[1] + " / " + data[2]
        stations.append((ident, name))
    return stations


def get_by_stations() -> tuple[str, str]:
    """Get all available stations for Bayern."""
    stations = []
    data = fetch_soup("https://www.hnd.bayern.de/pegel")
    boobls = data.find_all("img", class_="bobbl")
    for bobbl in boobls:
        ident = "BY_" + str(bobbl.get("id"))[1:]
        name = (
            str(bobbl.get("data-name")).strip()
            + " / "
            + str(bobbl.get("data-zeile2")).strip()
        )
        stations.append((ident, name))
    return stations


def get_hb_stations() -> tuple[str, str]:
    """Get all available stations for Bremen."""
    stations = []
    data = fetch_text(
        "https://geoportale.dp.dsecurecloud.de/pegelbremen", forced_encoding="utf-8"
    )
    js_file = data[data.find('<script src="') + 13 :].strip()
    js_file = js_file[: js_file.find('"></script>')].strip()
    js_url = "https://geoportale.dp.dsecurecloud.de/pegelbremen/" + js_file
    data = fetch_text(js_url, forced_encoding="utf-8")
    stations_string = data[data.find("pegelonlineStations:[") + 21 :].strip()
    stations_string = stations_string[: stations_string.find("],")].strip()
    stations_names = stations_string.split(",")
    stations_names = [station.replace('"', "") for station in stations_names]
    stations_names_upper = [station.upper() for station in stations_names]
    pe_stations = fetch_json(
        "https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations.json"
    )
    for pe_st in pe_stations:
        if pe_st["longname"] in stations_names_upper:
            ident = "HB_" + pe_st["number"]
            name = (
                stations_names[stations_names_upper.index(pe_st["longname"])]
                + " / "
                + pe_st["water"]["longname"].capitalize()
            )
            stations.append((ident, name))
    return stations


def get_he_stations() -> tuple[str, str]:
    """Get all available stations for Hessen."""
    stations = []
    data = fetch_json(
        "https://www.hlnug.de/static/pegel/wiskiweb3/data/internet/stations/stations.json"
    )
    for station in data:
        if len(station["WTO_OBJECT"].strip()) > 0:
            ident = "HE_" + station["station_no"]
            name = (
                station["station_name"].strip() + " / " + station["WTO_OBJECT"].strip()
            )
            stations.append((ident, name))
    return stations


def get_hh_stations() -> tuple[str, str]:
    """Get all available stations for Hamburg."""
    stations = []
    data = fetch_soup("https://www.wabiha.de/karte.html")
    tooltipwrapper = data.find("div", id="tooltipwrapper")
    divs = tooltipwrapper.find_all("div", class_="tooltip-content")
    for div in divs:
        spans = div.find_all("span")
        if len(spans) == 8:
            ident = "HH_" + div["id"].split("-")[-1]
            text = div.getText()
            name = text[: text.find("Gewässer:")].strip()
            name = (
                name
                + " / "
                + text[
                    text.find("Gewässer:") + 9 : text.find("Niederschlagsvorhersage")
                ].strip()
            )
            stations.append((ident, name))
    return stations


def get_mv_stations() -> tuple[str, str]:
    """Get all available stations for Mecklenburg-Vorpommern."""
    stations = []
    data = fetch_soup("https://pegelportal-mv.de/pegel_list.html")
    table = data.find("table", id="pegeltab")
    tbody = table.find("tbody")
    trs = tbody.find_all("tr")
    for row in trs:
        tds = row.find_all("td")
        if len(tds) > 1:
            name = tds[0].getText().strip() + " / " + tds[1].getText().strip()
            link = tds[6].find("a")
            if link is None:
                link = tds[7].find("a")
            if link is not None:
                href = link["href"]
                if href.find("pegelnummer=") != -1:
                    ident = href[href.find("pegelnummer=") + 12 :]
                    ident = "MV_" + ident[: ident.find("&")]
                elif href.find("pdf/pegelsteckbrief_") != -1:
                    ident = href[href.find("pdf/pegelsteckbrief_") + 20 :]
                    ident = "MV_" + ident[: ident.find(".pdf")]
                else:
                    ident = "MV_" + href[: href.rfind(".")]
                    if ident.find("-q") != -1:
                        ident = ident[: ident.find("-q")]
                stations.append((ident, name))
    return stations


def get_ni_stations() -> tuple[str, str]:
    """Get all available stations for Niedersachsen."""
    stations = []
    data = fetch_json(
        "https://bis.azure-api.net/PegelonlinePublic/REST/stammdaten"
        + "/stationen/All?key=9dc05f4e3b4a43a9988d747825b39f43"
    )
    for entry in data["getStammdatenResult"]:
        ident = "NI_" + entry["STA_Nummer"]
        name = entry["Name"].strip() + " / " + entry["GewaesserName"].strip()
        stations.append((ident, name))
    return stations


def get_nw_stations() -> tuple[str, str]:
    """Get all available stations for Nordrhein-Westfalen."""
    stations = []
    data = fetch_json(
        "https://hochwasserportal.nrw/lanuv/data/internet/stations/stations.json"
    )
    for station in data:
        if len(station["WTO_OBJECT"].strip()) > 0:
            ident = "NW_" + station["station_no"]
            name = (
                station["station_name"].strip() + " / " + station["WTO_OBJECT"].strip()
            )
            stations.append((ident, name))
    return stations


def get_rp_stations() -> tuple[str, str]:
    """Get all available stations for Rheinland-Pfalz."""
    stations = []
    data = fetch_json("https://hochwasser.rlp.de/api/v1/config")
    measurementsites = data["measurementsite"]
    rivers = data["rivers"]
    for key in measurementsites:
        site = measurementsites[key]
        ident = "RP_" + site["number"]
        name = site["name"] + " / " + rivers[site["rivers"][0]]["name"]
        stations.append((ident, name))
    return stations


def get_sh_stations() -> tuple[str, str]:
    """Get all available stations for Schleswig-Holstein."""
    stations = []
    data = fetch_soup("https://hsi-sh.de")
    search_string = re.compile("dialogheader-*")
    h1s = data.find_all("h1", id=search_string)
    for head in h1s:
        h1_text = head.getText().split()
        name = " ".join(h1_text[0 : len(h1_text) - 2])
        ident = "SH_" + h1_text[-1]
        d_list = head.find_next()
        for data in d_list:
            if (
                data.name == "dd"
                and data.attrs["class"][0] == "tooltip-content__gewaesser"
            ):
                name += " / " + data.getText().strip()
                break
        stations.append((ident, name))
    return stations


def get_sl_stations() -> tuple[str, str]:
    """Get all available stations for Saarland."""
    stations = []
    data = fetch_text(
        "https://iframe01.saarland.de/extern/wasser/Daten.js",
        forced_encoding="ISO-8859-1",
    )
    lines = data.split("\r\n")
    for line in lines:
        if line.find("Pegel(") != -1:
            content = line[line.find("Pegel(") + 6 : line.find(");")]
            content = content.replace("'", "")
            elements = content.split(",")
            if len(elements) == 9:
                ident = "SL_" + elements[2].strip()
                name = elements[4].strip() + " / " + elements[5].strip()
                stations.append((ident, name))
    return stations


def get_sn_stations() -> tuple[str, str]:
    """Get all available stations for Sachsen."""
    stations = []
    data = fetch_soup(
        "https://www.umwelt.sachsen.de/umwelt/infosysteme/hwims/portal/web/wasserstand-uebersicht"
    )
    karte = data.find_all("div", class_="karteWrapper")[0]
    links = karte.find_all("a", class_="msWrapper")
    for link in links:
        ident = "SN_" + link["href"].split("-")[-1]
        name = link.find_next("span", class_="popUpTitleBold").getText().strip()
        stations.append((ident, name))
    return stations


def get_st_stations() -> tuple[str, str]:
    """Get all available stations for Sachsen-Anhalt."""
    stations = []
    data = fetch_json(
        "https://hvz.lsaurl.de/fileadmin/Bibliothek/Politik_und_Verwaltung"
        + "/MLU/HVZ/KISTERS/data/internet/stations/stations.json"
    )
    for station in data:
        if len(station["WTO_OBJECT"].strip()) > 0:
            ident = "ST_" + station["station_no"]
            name = (
                station["station_name"].strip() + " / " + station["WTO_OBJECT"].strip()
            )
            stations.append((ident, name))
    return stations


def get_th_stations() -> tuple[str, str]:
    """Get all available stations for Thüringen."""
    stations = []
    data = fetch_soup("https://hnz.thueringen.de/hw-portal/thueringen.html")
    table = data.find_all("table", id="pegelTabelle")[0]
    tbody = table.find_all("tbody")[0]
    trs = tbody.find_all("tr")
    for row in trs:
        tds = row.find_all("td")
        if len(tds) > 10:
            ident = "TH_" + tds[1].getText().strip()
            name = tds[2].getText().strip() + " / " + tds[3].getText().strip()
            stations.append((ident, name))
    return stations


# Fetch and sort all available stations
all_stations = []
print("Fetching BB")
all_stations.extend(get_bb_stations())
print("Fetching BE")
all_stations.extend(get_be_stations())
print("Fetching BW")
all_stations.extend(get_bw_stations())
print("Fetching BY")
all_stations.extend(get_by_stations())
print("Fetching HB")
all_stations.extend(get_hb_stations())
print("Fetching HE")
all_stations.extend(get_he_stations())
print("Fetching HH")
all_stations.extend(get_hh_stations())
print("Fetching MV")
all_stations.extend(get_mv_stations())
print("Fetching NI")
all_stations.extend(get_ni_stations())
print("Fetching NW")
all_stations.extend(get_nw_stations())
print("Fetching RP")
all_stations.extend(get_rp_stations())
print("Fetching SH")
all_stations.extend(get_sh_stations())
print("Fetching SL")
all_stations.extend(get_sl_stations())
print("Fetching SN")
all_stations.extend(get_sn_stations())
print("Fetching ST")
all_stations.extend(get_st_stations())
print("Fetching TH")
all_stations.extend(get_th_stations())

all_stations.sort(key=lambda x: x[0])

print("Updating pegel.md")
with open("pegel.md", "w", encoding="utf-8") as f:
    print("| Pegel | Description |", file=f)
    print("|-------|-------------|", file=f)
    for pegel in all_stations:
        output = "| " + pegel[0] + " | " + pegel[1] + " |"
        print(output, file=f)

    f.close()
