"""The Länderübergreifendes Hochwasser Portal API."""

from __future__ import annotations
from .const import API_TIMEOUT, LOGGER
import datetime
import requests
import bs4
import traceback
import json
import re


class HochwasserPortalAPI:
    """API to retrieve the data."""

    def __init__(self, ident) -> None:
        """Initialize the API."""
        self.ident = ident
        self.name = None
        self.level = None
        self.stage = None
        self.flow = None
        self.internal_url = None
        self.url = None
        self.hint = None
        self.stage_levels = [None] * 4
        self.last_update = None
        self.data_valid = False
        if len(ident) > 3:
            self.parse_init()
            self.update()
        if self.data_valid:
            LOGGER.debug("Init API - %s (%s) - Done!", self.ident, self.name)
        else:
            LOGGER.error("Init API - %s - Failed!", self.ident)

    def __bool__(self):
        """Return the data_valid attribute."""
        return self.data_valid

    def __repr__(self):
        """Return the representation."""
        if self.name is not None:
            return f"{self.name} ({self.ident})"
        return self.ident

    def fetch_json(self, url):
        """Fetch data via json."""
        try:
            response = requests.get(url, timeout=API_TIMEOUT)
            response.raise_for_status()
            json_data = response.json()
            return json_data
        except:
            # Don't care about errors because in some cases the requested page doesn't exist
            return None

    def fetch_soup(self, url, remove_xml=False):
        """Fetch data via soup."""
        try:
            response = requests.get(url, timeout=API_TIMEOUT)
            # Override encoding by real educated guess (required for SH)
            response.encoding = response.apparent_encoding
            response.raise_for_status()
            if remove_xml and (
                (response.text.find('<?xml version="1.0" encoding="ISO-8859-15" ?>'))
                == 0
            ):
                text = response.text[response.text.find("<!DOCTYPE html>") :]
                soup = bs4.BeautifulSoup(text, "lxml")
            else:
                soup = bs4.BeautifulSoup(response.text, "lxml")
            return soup
        except:
            # Don't care about errors because in some cases the requested page doesn't exist
            return None

    def fetch_text(self, url, forced_encoding=None):
        """Fetch data via text."""
        try:
            response = requests.get(url, timeout=API_TIMEOUT)
            if forced_encoding is not None:
                response.encoding = forced_encoding
            else:
                # Override encoding by real educated guess (required for BW)
                response.encoding = response.apparent_encoding
            response.raise_for_status()
            return response.text
        except:
            # Don't care about errors because in some cases the requested page doesn't exist
            return None

    def fix_bb_encoding(self, input):
        """Fix utf-8 encoding for BB"""
        replace = False
        cnt = 0
        output = ""
        for c in input:
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
                        output = output + chr(92)
                        output = output + chr(num)
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
                        output = output + chr(new_num)
                        replace = False
            else:
                output = output + chr(num)
        return output

    def calc_stage(self):
        """Calc stage from level and stage levels."""
        if all(sl is None for sl in self.stage_levels):
            self.stage = None
        else:
            if (self.stage_levels[3] is not None) and (
                self.level > self.stage_levels[3]
            ):
                self.stage = 4
            elif (self.stage_levels[2] is not None) and (
                self.level > self.stage_levels[2]
            ):
                self.stage = 3
            elif (self.stage_levels[1] is not None) and (
                self.level > self.stage_levels[1]
            ):
                self.stage = 2
            elif (self.stage_levels[0] is not None) and (
                self.level > self.stage_levels[0]
            ):
                self.stage = 1
            else:
                self.stage = 0

    def parse_init_BB(self):
        """Parse data for Brandenburg."""
        try:
            # Get data
            page = self.fetch_text("https://pegelportal.brandenburg.de/start.php")
            lines = page.split("\n")
            # Parse data
            start_found = False
            for line in lines:
                line = line.strip()
                if line == "pkz: '" + self.ident[3:] + "',":
                    start_found = True
                    continue
                if start_found:
                    if line == "}),":
                        break
                    if line.count("'") == 2:
                        key = line[: line.find(":")]
                        value = line.split("'")[1]
                        if key == "name":
                            self.name = self.fix_bb_encoding(str(value))
                        elif key == "gewaesser":
                            self.name = (
                                self.name + " / " + self.fix_bb_encoding(str(value))
                            )
                        elif key == "fgid":
                            self.url = (
                                "https://pegelportal.brandenburg.de/messstelle.php?fgid="
                                + str(value)
                                + "&pkz="
                                + self.ident[3:]
                            )
                            break
        except Exception as e:
            LOGGER.error(
                "An error occured while fetching init data for %s: %s", self.ident, e
            )

    def parse_BB(self):
        """Parse data for Brandenburg."""
        try:
            # Get data
            page = self.fetch_text("https://pegelportal.brandenburg.de/start.php")
            lines = page.split("\n")
            # Parse data
            start_found = False
            prev_line = None
            for line in lines:
                line = line.strip()
                if line == "pkz: '" + self.ident[3:] + "',":
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
                                self.stage = int(value)
                            except:
                                self.stage = None
                        else:
                            self.stage = None
                    elif key == "datum":
                        timestamp = str(value)
                    elif key == "zeit":
                        timestamp = timestamp + " " + str(value)
                        try:
                            self.last_update = datetime.datetime.strptime(
                                timestamp, "%d.%m.%Y %H:%M"
                            )
                        except:
                            self.last_update = None
                    elif key == "wert":
                        try:
                            self.level = float(value.replace(",", "."))
                        except:
                            self.level = None
                    elif key == "qwert":
                        try:
                            self.flow = float(value.replace(",", "."))
                        except:
                            self.flow = None
                        break
                prev_line = line
            if self.last_update is not None:
                self.data_valid = True
            else:
                self.data_valid = False
        except Exception as e:
            self.level = None
            self.stage = None
            self.last_update = None
            self.data_valid = False
            LOGGER.error(
                "An error occured while fetching data for %s: %s", self.ident, e
            )

    def parse_init_BE(self):
        """Parse data for Berlin."""
        try:
            # Get data
            page = self.fetch_soup(
                "https://wasserportal.berlin.de/start.php?anzeige=tabelle_ow&messanzeige=ms_ow_berlin",
                remove_xml=True,
            )
            # Parse data
            table = page.find("table", id="pegeltab")
            tbody = table.find("tbody")
            trs = tbody.find_all("tr")
            for tr in trs:
                tds = tr.find_all("td")
                if len(tds) == 10:
                    if (tds[0].getText().strip() == self.ident[3:]) and (
                        tds[0].find_next("a")["href"][:12] == "station.php?"
                    ):
                        self.url = (
                            "https://wasserportal.berlin.de/"
                            + tds[0].find_next("a")["href"]
                        )
                        self.name = (
                            tds[1].getText().strip() + " / " + tds[4].getText().strip()
                        )
                        break
        except Exception as e:
            LOGGER.error(
                "An error occured while fetching init data for %s: %s", self.ident, e
            )

    def parse_BE(self):
        """Parse data for Berlin."""
        try:
            # Get data and parse level data
            yesterday = datetime.date.today() - datetime.timedelta(days=1)
            query = (
                self.url + "&sreihe=ew&smode=c&sdatum=" + yesterday.strftime("%d.%m.%Y")
            )
            data = self.fetch_text(query)
            lines = data.split("\n")
            lines.reverse()
            self.level = None
            self.last_update = None
            for line in lines:
                if len(line) > 0:
                    values = line.split(";")
                    if len(values) == 2:
                        try:
                            self.level = float(values[1].replace(",", "."))
                            if int(self.level) != -777:
                                self.last_update = datetime.datetime.strptime(
                                    values[0], '"%d.%m.%Y %H:%M"'
                                )
                                break
                        except:
                            continue
            # Get data and parse flow data
            query = query.replace("thema=ows", "thema=odf")
            query = query.replace("thema=wws", "thema=wdf")
            data = self.fetch_text(query)
            lines = data.split("\n")
            lines.reverse()
            self.flow = None
            for line in lines:
                if len(line) > 0:
                    values = line.split(";")
                    if len(values) == 2:
                        try:
                            self.flow = float(values[1].replace(",", "."))
                            if int(self.flow) != -777:
                                if self.last_update is None:
                                    self.last_update = datetime.datetime.strptime(
                                        values[0], '"%d.%m.%Y %H:%M"'
                                    )
                                break
                        except:
                            continue
            if self.last_update is not None:
                self.data_valid = True
            else:
                self.data_valid = False
        except Exception as e:
            self.level = None
            self.flow = None
            self.last_update = None
            self.data_valid = False
            LOGGER.error(
                "An error occured while fetching data for %s: %s", self.ident, e
            )

    def parse_init_BW(self):
        """Parse data for Baden-Württemberg."""
        try:
            # Get data
            page = self.fetch_text(
                "https://www.hvz.baden-wuerttemberg.de/js/hvz_peg_stmn.js"
            )
            lines = page.split("\r\n")[6:-4]
            # Parse data
            for line in lines:
                # Building a valid json string
                content = line[line.find("[") : (line.find("]") + 1)]
                content = content.replace("'", '"')
                content = '{ "data":' + content + "}"
                data = json.loads(content)["data"]
                if data[0] == self.ident[3:]:
                    self.name = data[1] + " / " + data[2]
                    self.url = (
                        "https://hvz.baden-wuerttemberg.de/pegel.html?id="
                        + self.ident[3:]
                    )
                    if float(data[24]) > 0.0:
                        self.stage_levels[0] = round(float(data[24]) * 100.0, 0)
                    if data[30] > 0:
                        if (self.stage_levels[0] is None) or (
                            float(data[30]) < self.stage_levels[0]
                        ):
                            self.stage_levels[0] = float(data[30])
                    if data[31] > 0:
                        self.stage_levels[1] = float(data[31])
                    if data[32] > 0:
                        self.stage_levels[2] = float(data[32])
                    if data[33] > 0:
                        self.stage_levels[3] = float(data[33])
                    LOGGER.debug("Stage levels : %s", self.stage_levels)
                    break
        except Exception as e:
            LOGGER.error(
                "An error occured while fetching init data for %s: %s", self.ident, e
            )

    def parse_BW(self):
        """Parse data for Baden-Württemberg."""
        try:
            # Get data
            page = self.fetch_text(
                "https://www.hvz.baden-wuerttemberg.de/js/hvz_peg_stmn.js"
            )
            lines = page.split("\r\n")[6:-4]
            # Parse data
            self.last_update = None
            for line in lines:
                # Building a valid json string
                content = line[line.find("[") : (line.find("]") + 1)]
                content = content.replace("'", '"')
                content = '{ "data":' + content + "}"
                data = json.loads(content)["data"]
                if data[0] == self.ident[3:]:
                    try:
                        if data[5] == "cm":
                            self.level = float(data[4])
                            self.calc_stage()
                            try:
                                dt = data[6].split()
                                self.last_update = datetime.datetime.strptime(
                                    dt[0] + dt[1], "%d.%m.%Y%H:%M"
                                )
                            except:
                                self.last_update = None
                        else:
                            self.level = None
                            self.stage = None
                    except:
                        self.level = None
                        self.stage = None
                    try:
                        if data[8] == "m³/s":
                            self.flow = float(data[7])
                        else:
                            self.flow = None
                    except:
                        self.flow = None
                    if self.last_update is None:
                        try:
                            dt = data[9].split()
                            self.last_update = datetime.datetime.strptime(
                                dt[0] + dt[1], "%d.%m.%Y%H:%M"
                            )
                        except:
                            self.last_update = None
                    break
            self.data_valid = True
        except Exception as e:
            self.data_valid = False
            LOGGER.error(
                "An error occured while fetching data for %s: %s", self.ident, e
            )

    def parse_init_BY(self):
        """Parse data for Bayern."""
        try:
            # Get data
            soup = self.fetch_soup("https://www.hnd.bayern.de/pegel")
            img_id = "p" + self.ident[3:]
            imgs = soup.find_all("img", id=img_id)
            data = imgs[0]
            # Parse data
            self.name = data.get("data-name")
            if len(data.get("data-zeile2")) > 0:
                self.name += " / " + data.get("data-zeile2")
            self.url = data.parent.attrs["href"]
        except Exception as e:
            LOGGER.error(
                "An error occured while fetching init data for %s: %s", self.ident, e
            )

    def parse_BY(self):
        """Parse data for Bayern."""
        self.level = None
        self.flow = None
        self.stage = None
        try:
            # Get data
            soup = self.fetch_soup("https://www.hnd.bayern.de/pegel")
            img_id = "p" + self.ident[3:]
            imgs = soup.find_all("img", id=img_id)
            data = imgs[0]
            # Parse data
            if len(data.get("data-wert")) > 0:
                self.level = float(str(data.get("data-wert")).replace(",", "."))
            else:
                self.level = None
            if len(data.get("data-wert2")) > 0:
                self.flow = float(str(data.get("data-wert2")).replace(",", "."))
            else:
                self.flow = None
            if len(data.get("data-ms")) > 0:
                self.stage = int(data.get("data-ms"))
            else:
                self.stage = None
            self.hint = data.get("data-stoerung")
            if len(data.get("data-datum")) > 0:
                try:
                    self.last_update = datetime.datetime.strptime(
                        data.get("data-datum"), "%d.%m.%Y, %H:%M"
                    )
                except:
                    self.last_update = None
            else:
                self.last_update = None
            self.data_valid = True
        except Exception as e:
            self.data_valid = False
            LOGGER.error(
                "An error occured while fetching data for %s: %s", self.ident, e
            )

    def parse_init_HB(self):
        """Parse data for Bremen."""
        try:
            # Get data from Pegelstände Bremen
            pb_page = self.fetch_text(
                "https://geoportale.dp.dsecurecloud.de/pegelbremen/src.2c9c6cd7.js",
                forced_encoding="utf-8",
            )
            # Get data from PegelOnline
            pe_stations = self.fetch_json(
                "https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations.json"
            )
            # Parse data - Get list of stations
            stations_string = pb_page[
                pb_page.find("pegelonlineStations:[") + 21 :
            ].strip()
            stations_string = stations_string[: stations_string.find("],")].strip()
            stations = stations_string.split(",")
            stations_names = [station.replace('"', "") for station in stations]
            stations_names_upper = [station.upper() for station in stations_names]
            # Parse data - Collect data from PegelOnlie
            for pe in pe_stations:
                if pe["number"] == self.ident[3:]:
                    station_name = stations_names[
                        stations_names_upper.index(pe["longname"])
                    ]
                    self.name = (
                        station_name + " / " + pe["water"]["longname"].capitalize()
                    )
                    self.internal_url = (
                        "https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations/"
                        + pe["uuid"]
                        + "/W/measurements.json?start=P1D"
                    )
                    self.url = (
                        "https://pegelonline.wsv.de/webservices/zeitreihe/visualisierung?pegeluuid="
                        + pe["uuid"]
                    )
                    break
            # Parse data - Collect stage levels from Pegelstände Bremen
            prop_string = pb_page[pb_page.find("Stations:{") + 10 :].strip()
            prop_string = prop_string[prop_string.find("properties:[") + 12 :].strip()
            prop_string = prop_string[: prop_string.find(")]}")].strip()
            prop_string = prop_string[prop_string.find(station_name) - 1 :].strip()
            prop_string = prop_string[: prop_string.find(")")].strip()
            if prop_string.find("[") != -1:
                sl_string = prop_string[
                    prop_string.find("[") + 1 : prop_string.find("]")
                ]
                self.stage_levels = sl_string.split(",")
                self.stage_levels = [float(sl) for sl in self.stage_levels]
                while len(self.stage_levels) < 4:
                    self.stage_levels.append(None)
            LOGGER.debug("Stage levels : %s", self.stage_levels)
        except Exception as e:
            LOGGER.error(
                "An error occured while fetching init data for %s: %s", self.ident, e
            )

    def parse_HB(self):
        """Parse data for Bremen."""
        try:
            # Get data
            data = self.fetch_json(self.internal_url)
            # Parse data
            if len(data) > 0:
                try:
                    self.level = float(data[-1]["value"])
                except:
                    self.level = None
                self.calc_stage()
                try:
                    self.last_update = datetime.datetime.fromisoformat(
                        data[-1]["timestamp"]
                    )
                except:
                    self.last_update = None
                self.data_valid = True
            else:
                self.level = None
                self.stage = None
                self.last_update = None
                self.data_valid = False
        except Exception as e:
            self.level = None
            self.stage = None
            self.last_update = None
            self.data_valid = False
            LOGGER.error(
                "An error occured while fetching data for %s: %s", self.ident, e
            )

    def parse_init_HE(self):
        """Parse data for Hessen."""
        try:
            # Get Stations Data
            he_stations = self.fetch_json(
                "https://www.hlnug.de/static/pegel/wiskiweb3/data/internet/stations/stations.json"
            )
            for station in he_stations:
                if station["station_no"] == self.ident[3:]:
                    self.name = (
                        station["station_name"].strip()
                        + " / "
                        + station["WTO_OBJECT"].strip()
                    )
                    self.url = (
                        "https://www.hlnug.de/static/pegel/wiskiweb3/webpublic/#/overview/Wasserstand/station/"
                        + station["station_id"]
                        + "/"
                        + station["station_name"]
                        + "/Wasserstand"
                    )
                    self.internal_url = (
                        "https://www.hlnug.de/static/pegel/wiskiweb3/data/internet/stations/"
                        + station["site_no"]
                        + "/"
                        + station["station_no"]
                    )
                    self.hint = station["INTERNET_BEMERKUNG"].strip()
                    if len(self.hint) == 0:
                        self.hint = None
                    break
        except Exception as e:
            LOGGER.error(
                "An error occured while fetching init data for %s: %s", self.ident, e
            )
            return
        try:
            # Get stage levels
            if self.internal_url is not None:
                alarmlevels = self.fetch_json(self.internal_url + "/W/alarmlevel.json")
                for station_data in alarmlevels:
                    if (
                        "ts_name" in station_data
                        and "data" in station_data
                        and isinstance(station_data["data"], list)
                        and len(station_data["data"]) > 0
                    ):
                        # Check if ts_name is one of the desired values
                        if station_data["ts_name"] == "Meldestufe1":
                            self.stage_levels[0] = float(station_data["data"][-1][1])
                        elif station_data["ts_name"] == "Meldestufe2":
                            self.stage_levels[1] = float(station_data["data"][-1][1])
                        # No equivalent to stage_levels[2] available
                        elif station_data["ts_name"] == "Meldestufe3":
                            self.stage_levels[3] = float(station_data["data"][-1][1])
                LOGGER.debug("Stage levels : %s", self.stage_levels)
        except:
            self.stage_levels = [None] * 4
            LOGGER.debug("%s: No stage levels available", self.ident)

    def parse_HE(self):
        """Parse data for Hessen."""
        if self.internal_url is None:
            self.level = None
            self.flow = None
            self.stage = None
            self.data_valid = False
            return

        last_update_str_w = None
        try:
            # Get data
            data = self.fetch_json(self.internal_url + "/W/week.json")
            # Parse data
            for dataset in data:
                if dataset["ts_name"] == "15.P":
                    last_update_str_w = dataset["data"][-1][0]
                    self.level = float(dataset["data"][-1][1])
                    self.calc_stage()
                    break
        except:
            self.level = None
            self.stage = None
            LOGGER.debug("%s: No level data available", self.ident)

        last_update_str_q = None
        try:
            # Get data
            data = self.fetch_json(self.internal_url + "/Q/week.json")
            # Parse data
            for dataset in data:
                if dataset["ts_name"] == "15.P":
                    last_update_str_q = dataset["data"][-1][0]
                    self.flow = float(dataset["data"][-1][1])
                    break
        except:
            self.flow = None
            LOGGER.debug("%s: No flow data available", self.ident)

        if self.level is not None:
            self.data_valid = True
            self.last_update = datetime.datetime.fromisoformat(last_update_str_w)
        elif self.level is not None:
            self.data_valid = True
            self.last_update = datetime.datetime.fromisoformat(last_update_str_q)
        else:
            self.data_valid = False
            LOGGER.error("An error occured while fetching data for %s", self.ident)

    def parse_init_HH(self):
        """Parse data for Hamburg."""
        try:
            # Get data
            soup = self.fetch_soup("https://www.wabiha.de/karte.html")
            tooltipwrapper = soup.find("div", id="tooltipwrapper")
            div = tooltipwrapper.find_next(
                "div", id="tooltip-content-" + self.ident[3:]
            )
            spans = div.find_all("span")
            # Parse data
            if len(spans) == 8:
                text = div.getText()
                self.name = text[: text.find("Gewässer:")].strip()
                self.name = (
                    self.name
                    + " / "
                    + text[
                        text.find("Gewässer:")
                        + 9 : text.find("Niederschlagsvorhersage")
                    ].strip()
                )
                self.url = "https://www.wabiha.de/grafik-" + self.ident[3:] + ".html"
        except Exception as e:
            LOGGER.error(
                "An error occured while fetching init data for %s: %s", self.ident, e
            )

    def parse_HH(self):
        """Parse data for Hamburg."""
        try:
            # Get data
            soup = self.fetch_soup("https://www.wabiha.de/karte.html")
            tooltipwrapper = soup.find("div", id="tooltipwrapper")
            div = tooltipwrapper.find_next(
                "div", id="tooltip-content-" + self.ident[3:]
            )
            spans = div.find_all("span")
            # Parse data
            self.last_update = None
            if len(spans) == 8:
                text = div.getText()
                try:
                    self.level = float(
                        text[
                            text.find("Wasserstand")
                            + 11 : text.find("[NHN\u00A0+/-\u00A0cm]")
                        ]
                        .replace(".", "")
                        .strip()
                    )
                except:
                    self.level = None
                try:
                    self.last_update = datetime.datetime.strptime(
                        text[
                            text.find("\u00A0\u00A0\u00A0 um") + 6 : text.find("Trend")
                        ].strip(),
                        "%d.%m.%Y %H:%M",
                    )
                except:
                    self.last_update = None
                try:
                    stage_in = int(spans[7].attrs["class"][-1].split("_")[-1])
                    if stage_in == 0:
                        self.stage = 0
                    elif stage_in == 1:
                        self.stage = 1
                    elif stage_in == 2:
                        self.stage = 3
                    else:
                        self.stage = None
                except:
                    self.stage = None
            if self.last_update is not None:
                self.data_valid = True
            else:
                self.data_valid = False
        except Exception as e:
            self.level = None
            self.stage = None
            self.last_update = None
            self.data_valid = False
            LOGGER.error(
                "An error occured while fetching data for %s: %s", self.ident, e
            )

    def parse_init_MV(self):
        """Parse data for Mecklenburg-Vorpommern."""
        try:
            # Get data
            soup = self.fetch_soup("https://pegelportal-mv.de/pegel_list.html")
            table = soup.find("table", id="pegeltab")
            tbody = table.find("tbody")
            search_string = re.compile(self.ident[3:])
            link = tbody.find_next("a", href=search_string)
            tr = link.parent.parent
            tds = tr.find_all("td")
            # Parse data
            cnt = 0
            for td in tds:
                if cnt == 0:
                    self.name = td.getText().strip()
                elif cnt == 1:
                    self.name += " / " + td.getText().strip()
                    break
                cnt += 1
            if self.ident.find(".") != -1:
                self.url = "https://pegelportal-mv.de/" + self.ident[3:] + ".html"
            else:
                self.url = link["href"]
        except Exception as e:
            LOGGER.error(
                "An error occured while fetching init data for %s: %s", self.ident, e
            )

    def parse_MV(self):
        """Parse data for Mecklenburg-Vorpommern."""
        try:
            # Get data
            soup = self.fetch_soup("https://pegelportal-mv.de/pegel_list.html")
            table = soup.find("table", id="pegeltab")
            tbody = table.find("tbody")
            search_string = re.compile(self.ident[3:])
            link = tbody.find_next("a", href=search_string)
            tr = link.parent.parent
            tds = tr.find_all("td")
            # Parse data
            cnt = 0
            for td in tds:
                if cnt == 2:
                    try:
                        self.last_update = datetime.datetime.strptime(
                            td.getText().strip(), "%d.%m.%Y %H:%M"
                        )
                    except:
                        self.last_update = None
                elif cnt == 3:
                    try:
                        self.level = float(td.getText().strip())
                    except:
                        self.level = None
                elif cnt == 4:
                    try:
                        self.flow = float(td.getText().strip())
                    except:
                        self.flow = None
                    img = td.find_next("img")
                    try:
                        splits = img["title"].strip().split()
                        if splits[0] == "Pegel-Stufe":
                            self.stage = int(splits[1]) - 4
                            if self.stage < 0:
                                self.stage = 0
                        else:
                            self.stage = None
                    except:
                        self.stage = None
                    break
                cnt += 1
            if self.last_update is not None:
                self.data_valid = True
            else:
                self.data_valid = False
        except Exception as e:
            self.level = None
            self.flow = None
            self.stage = None
            self.last_update = None
            self.data_valid = False
            LOGGER.error(
                "An error occured while fetching data for %s: %s", self.ident, e
            )

    def parse_init_NI(self):
        """Parse data for Niedersachsen."""
        try:
            # Get data
            data = self.fetch_json(
                "https://bis.azure-api.net/PegelonlinePublic/REST/stammdaten/stationen/All?key=9dc05f4e3b4a43a9988d747825b39f43"
            )
            # Parse data
            for entry in data["getStammdatenResult"]:
                if entry["STA_Nummer"] == self.ident[3:]:
                    self.name = entry["Name"] + " / " + entry["GewaesserName"]
                    self.internal_url = (
                        "https://bis.azure-api.net/PegelonlinePublic/REST/stammdaten/stationen/"
                        + str(entry["STA_ID"])
                        + "?key=9dc05f4e3b4a43a9988d747825b39f43"
                    )
                    self.url = (
                        "https://www.pegelonline.nlwkn.niedersachsen.de/Pegel/Karte/Binnenpegel/ID/"
                        + str(entry["STA_ID"])
                    )
                    if entry["Internetbeschreibung"] != "Keine Daten":
                        self.hint = entry["Internetbeschreibung"]
                    else:
                        self.hint = None
                    break
        except Exception as e:
            LOGGER.error(
                "An error occured while fetching init data for %s: %s", self.ident, e
            )

    def parse_NI(self):
        """Parse data for Niedersachsen."""
        if self.internal_url is None:
            return

        try:
            # Get data
            data = self.fetch_json(self.internal_url)
            # Parse data
            try:
                self.stage = int(
                    data["getStammdatenResult"][0]["Parameter"][0]["Datenspuren"][0][
                        "AktuelleMeldeStufe"
                    ]
                )
            except (IndexError, KeyError, TypeError):
                self.stage = None
            try:
                value = float(
                    data["getStammdatenResult"][0]["Parameter"][0]["Datenspuren"][0][
                        "AktuellerMesswert"
                    ]
                )
            except (IndexError, KeyError, TypeError):
                value = None
            try:
                if data["getStammdatenResult"][0]["Parameter"][0]["Einheit"] == "cm":
                    self.level = value
                    self.flow = None
                elif (
                    data["getStammdatenResult"][0]["Parameter"][0]["Einheit"] == "m³/s"
                ):
                    self.level = None
                    self.flow = value
                else:
                    self.level = None
                    self.flow = None
            except (IndexError, KeyError, TypeError):
                self.level = None
                self.flow = None
            try:
                self.last_update = datetime.datetime.strptime(
                    data["getStammdatenResult"][0]["Parameter"][0]["Datenspuren"][0][
                        "AktuellerMesswert_Zeitpunkt"
                    ],
                    "%d.%m.%Y %H:%M",
                )
            except (IndexError, KeyError, TypeError):
                self.last_update = None
            self.data_valid = True
        except Exception as e:
            self.data_valid = False
            LOGGER.error(
                "An error occured while fetching data for %s: %s", self.ident, e
            )

    def parse_init_NW(self):
        """Parse data for Nordrhein-Westfalen."""
        try:
            # Get Stations Data
            nw_stations = self.fetch_json(
                "https://hochwasserportal.nrw/lanuv/data/internet/stations/stations.json"
            )
            for station in nw_stations:
                if station["station_no"] == self.ident[3:]:
                    self.name = station["station_name"] + " / " + station["WTO_OBJECT"]
                    self.internal_url = (
                        "https://hochwasserportal.nrw/lanuv/data/internet/stations/"
                        + station["site_no"]
                        + "/"
                        + station["station_no"]
                    )
                    self.url = (
                        "https://hochwasserportal.nrw/lanuv/webpublic/index.html#/overview/Wasserstand/station/"
                        + station["station_id"]
                        + "/"
                        + station["station_name"]
                    )
                    break
            # Get stage levels
            if self.internal_url is not None:
                nw_stages = self.fetch_json(self.internal_url + "/S/alarmlevel.json")
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
                            self.stage_levels[0] = float(station_data["data"][-1][1])
                        elif station_data["ts_name"] == "W.Informationswert_2":
                            self.stage_levels[1] = float(station_data["data"][-1][1])
                        elif station_data["ts_name"] == "W.Informationswert_3":
                            self.stage_levels[2] = float(station_data["data"][-1][1])
                LOGGER.debug("Stage levels : %s", self.stage_levels)
        except Exception as e:
            LOGGER.error(
                "An error occured while fetching init data for %s: %s", self.ident, e
            )

    def parse_NW(self):
        """Parse data for Nordrhein-Westfalen."""
        if self.url is None:
            self.level = None
            self.flow = None
            self.stage = None
            self.data_valid = False
            return

        try:
            # Get data
            data = self.fetch_json(self.internal_url + "/S/week.json")
            # Parse data
            self.level = float(data[0]["data"][-1][1])
            self.calc_stage()
            self.hint = None
            if len(data[0]["AdminStatus"].strip()) > 0:
                self.hint = data[0]["AdminStatus"].strip()
            if len(data[0]["AdminBemerkung"].strip()) > 0:
                if len(self.hint) > 0:
                    self.hint += " / " + data[0]["AdminBemerkung"].strip()
                else:
                    self.hint = data[0]["AdminBemerkung"].strip()
            # Extract the last update timestamp from the JSON data
            last_update_str = data[0]["data"][-1][0]
            # Convert the string timestamp to a datetime object
            self.last_update = datetime.datetime.fromisoformat(last_update_str)
            self.data_valid = True
        except Exception as e:
            self.level = None
            self.stage = None
            self.hint = None
            self.data_valid = False
            LOGGER.error(
                "An error occured while fetching data for %s: %s %s",
                self.ident,
                e,
                traceback.format_exc(),
            )

    def parse_init_RP(self):
        """Parse data for Rheinland-Pfalz."""
        try:
            # Get data
            data = self.fetch_json("https://hochwasser.rlp.de/api/v1/config")
            measurementsites = data["measurementsite"]
            rivers = data["rivers"]
            riverareas = data["riverareas"]
            thresholds = data["legends"]["thresholds"]
            # Parse data
            for key in measurementsites:
                site = measurementsites[key]
                if site["number"] == self.ident[3:]:
                    self.name = site["name"] + " / " + rivers[site["rivers"][0]]["name"]
                    self.url = (
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
                        self.stage_levels[0] = thresholds[key]["W"]["22"]
                        self.stage_levels[1] = thresholds[key]["W"]["21"]
                        self.stage_levels[2] = thresholds[key]["W"]["20"]
                        self.stage_levels[3] = thresholds[key]["W"]["19"]
                    except:
                        self.stage_levels = [None] * 4
                    LOGGER.debug("Stage levels : %s", self.stage_levels)
                    break
        except Exception as e:
            LOGGER.error(
                "An error occured while fetching init data for %s: %s", self.ident, e
            )

    def parse_RP(self):
        """Parse data for Rheinland-Pfalz."""
        try:
            # Get data
            data = self.fetch_json(
                "https://hochwasser.rlp.de/api/v1/measurement-site/" + self.ident[3:]
            )
            # Parse data
            last_update_str = None
            try:
                self.level = float(data["W"]["yLast"])
                self.calc_stage()
                last_update_str = data["W"]["xLast"][:-1] + "+00:00"
            except:
                self.level = None
                self.stage = None
            try:
                self.flow = float(data["Q"]["yLast"])
                if last_update_str is None:
                    last_update_str = data["Q"]["xLast"][:-1] + "+00:00"
            except:
                self.flow = None
            if last_update_str is not None:
                self.last_update = datetime.datetime.fromisoformat(last_update_str)
                self.data_valid = True
            else:
                self.last_update = None
                self.data_valid = False
        except Exception as e:
            LOGGER.error(
                "An error occured while fetching data for %s: %s", self.ident, e
            )

    def parse_init_SH(self):
        """Parse data for Schleswig-Holstein."""
        try:
            # Get data
            soup = self.fetch_soup("https://hsi-sh.de")
            search_string = "dialogheader-" + self.ident[3:]
            headings = soup.find_all("h1", id=search_string)
            # Parse data
            heading = headings[0]
            heading_text = heading.getText().split()
            self.name = " ".join(heading_text[0 : len(heading_text) - 2])
            d_list = heading.find_next()
            for element in d_list:
                if (
                    element.name == "dd"
                    and element.attrs["class"][0] == "tooltip-content__gewaesser"
                ):
                    self.name += " / " + element.getText()
            paragraph = heading.find_next("p", class_="tooltip-content__link")
            link = paragraph.find_next("a")
            if link["href"][0] == ".":
                self.url = "https://hsi-sh.de/" + link["href"][2:]
            else:
                self.url = link["href"]
        except Exception as e:
            LOGGER.error(
                "An error occured while fetching init data for %s: %s", self.ident, e
            )

    def parse_SH(self):
        """Parse data for Schleswig-Holstein."""
        self.level = None
        self.flow = None
        self.stage = None
        self.last_update = None
        try:
            # Get data
            soup = self.fetch_soup("https://hsi-sh.de")
            search_string = "dialogheader-" + self.ident[3:]
            headings = soup.find_all("h1", id=search_string)
            # Parse data
            heading = headings[0]
            if heading.attrs["class"][1].count("_") == 3:
                self.stage = int(heading.attrs["class"][1].split("_")[-1]) - 5
                if self.stage < 0:
                    self.stage = 0
            d_list = heading.find_next()
            for element in d_list:
                if (
                    element.name == "dd"
                    and element.attrs["class"][0] == "tooltip-content__w"
                ):
                    element_text = element.getText().split()
                    if element_text[1] == "cm":
                        self.level = float(element_text[0].replace(",", "."))
                        if element_text[4] == "(MEZ)":
                            self.last_update = datetime.datetime.strptime(
                                element_text[2] + element_text[3] + "+0100",
                                "%d.%m.%Y%H:%M%z",
                            )
                        else:
                            self.last_update = datetime.datetime.strptime(
                                element_text[2] + element_text[3], "%d.%m.%Y%H:%M"
                            )
                if (
                    element.name == "dd"
                    and element.attrs["class"][0] == "tooltip-content__q"
                ):
                    element_text = element.getText().split()
                    if element_text[1] == "m3/s":
                        self.flow = float(element_text[0].replace(",", "."))
            self.data_valid = True
        except Exception as e:
            self.data_valid = False
            LOGGER.error(
                "An error occured while fetching data for %s: %s", self.ident, e
            )

    def parse_init_SL(self):
        """Parse data for Saarland."""
        try:
            # Get data
            page = self.fetch_text(
                "https://iframe01.saarland.de/extern/wasser/Daten.js"
            )
            lines = page.split("\r\n")
            # Parse data
            for line in lines:
                if (line.find("Pegel(") != -1) and (line.find(self.ident[3:]) != -1):
                    content = line[line.find("Pegel(") + 6 : line.find(");")]
                    content = content.replace("'", "")
                    elements = content.split(",")
                    if len(elements) == 9:
                        self.name = elements[4].strip() + " / " + elements[5].strip()
                        self.url = (
                            "https://iframe01.saarland.de/extern/wasser/L"
                            + self.ident[3:]
                            + ".htm"
                        )
                        break
        except Exception as e:
            LOGGER.error(
                "An error occured while fetching init data for %s: %s", self.ident, e
            )

    def parse_SL(self):
        """Parse data for Saarland."""
        try:
            # Get data
            page = self.fetch_text(
                "https://iframe01.saarland.de/extern/wasser/Daten.js"
            )
            lines = page.split("\r\n")
            # Parse data
            for line in lines:
                if (line.find("Pegel(") != -1) and (line.find(self.ident[3:]) != -1):
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
                                self.stage = 4
                            elif (stage_int > 0) and (stage_int < 5):
                                self.stage = stage_int - 1
                            else:
                                self.stage = None
                        except:
                            self.stage = None
                        try:
                            self.level = float(elements[6].strip())
                        except:
                            self.level = None
                        try:
                            self.last_update = datetime.datetime.strptime(
                                elements[7].strip() + "+0100", "%d.%m.%Y %H:%M%z"
                            )
                        except:
                            self.last_update = None
                        break
            if self.last_update is not None:
                self.data_valid = True
            else:
                self.data_valid = False
        except Exception as e:
            self.level = None
            self.stage = None
            self.last_update = None
            self.data_valid = False
            LOGGER.error(
                "An error occured while fetching data for %s: %s", self.ident, e
            )

    def parse_init_SN(self):
        """Parse data for Sachsen."""
        try:
            # Get data
            soup = self.fetch_soup(
                "https://www.umwelt.sachsen.de/umwelt/infosysteme/hwims/portal/web/wasserstand-uebersicht"
            )
            karte = soup.find_all("div", class_="karteWrapper")[0]
            link = karte.find_all("a", href="wasserstand-pegel-" + self.ident[3:])[0]
            # Parse data
            self.name = (
                link.find_next("span", class_="popUpTitleBold").getText().strip()
            )
            self.url = (
                "https://www.umwelt.sachsen.de/umwelt/infosysteme/hwims/portal/web/"
                + link["href"]
            )
        except Exception as e:
            LOGGER.error(
                "An error occured while fetching init data for %s: %s", self.ident, e
            )

    def parse_SN(self):
        """Parse data for Sachsen."""
        try:
            # Get data
            soup = self.fetch_soup(
                "https://www.umwelt.sachsen.de/umwelt/infosysteme/hwims/portal/web/wasserstand-uebersicht"
            )
            karte = soup.find_all("div", class_="karteWrapper")[0]
            link = karte.find_all("a", href="wasserstand-pegel-" + self.ident[3:])[0]
            # Parse data
            if "meldePegel" in link.attrs["class"]:
                stage_colors = {
                    "#b38758": 0,
                    "#c5e566": 0,
                    "#ffeb3b": 1,
                    "#fb8a00": 2,
                    "#e53835": 3,
                    "#d400f9": 4,
                }
                data = link.find_next("div", class_="popUpStatus")
                try:
                    color = data.attrs["style"].split()[-1]
                    if color in stage_colors:
                        self.stage = stage_colors[color]
                    else:
                        self.stage = None
                except:
                    self.stage = None
            else:
                self.stage = None
            head = link.find_next("span", string="Wasserstand:")
            data = head.find_next("span", class_="popUpValue")
            try:
                self.level = float(data.getText().split()[0])
            except:
                self.level = None
            head = link.find_next("span", string="Durchfluss:")
            data = head.find_next("span", class_="popUpValue")
            try:
                self.flow = float(data.getText().split()[0].replace(",", "."))
            except:
                flow = None
            head = link.find_next("span", string="Datum:")
            data = head.find_next("span", class_="popUpValue")
            try:
                self.last_update = datetime.datetime.strptime(
                    data.getText().strip().split()[0], "%d.%m.%Y%H:%M"
                )
            except:
                self.last_update = None
            self.data_valid = True
        except Exception as e:
            self.level = None
            self.flow = None
            self.stage = None
            self.data_valid = False
            LOGGER.error(
                "An error occured while fetching data for %s: %s", self.ident, e
            )

    def parse_init_ST(self):
        """Parse data for Sachsen-Anhalt."""
        try:
            # Get Stations Data
            st_stations = self.fetch_json(
                "https://hvz.lsaurl.de/fileadmin/Bibliothek/Politik_und_Verwaltung/MLU/HVZ/KISTERS/data/internet/stations/stations.json"
            )
            for station in st_stations:
                if station["station_no"] == self.ident[3:]:
                    self.name = (
                        station["station_name"].strip()
                        + " / "
                        + station["WTO_OBJECT"].strip()
                    )
                    self.url = "https://hvz.lsaurl.de/#" + self.ident[3:]
                    self.internal_url = (
                        "https://hvz.lsaurl.de/fileadmin/Bibliothek/Politik_und_Verwaltung/MLU/HVZ/KISTERS/data/internet/stations/"
                        + station["site_no"]
                        + "/"
                        + self.ident[3:]
                    )
                    self.hint = (
                        station["web_anmerkung"].strip()
                        + " "
                        + station["web_wichtigerhinweis"].strip()
                    ).strip()
                    if len(self.hint) == 0:
                        self.hint = None
                    break
        except Exception as e:
            LOGGER.error(
                "An error occured while fetching init data for %s: %s", self.ident, e
            )
            return
        try:
            # Get stage levels
            if self.internal_url is not None:
                alarmlevels = self.fetch_json(self.internal_url + "/W/alarmlevel.json")
                for station_data in alarmlevels:
                    if (
                        "ts_name" in station_data
                        and "data" in station_data
                        and isinstance(station_data["data"], list)
                        and len(station_data["data"]) > 0
                    ):
                        # Check if ts_name is one of the desired values
                        if station_data["ts_name"] == "Alarmstufe 1":
                            self.stage_levels[0] = float(station_data["data"][-1][1])
                        elif station_data["ts_name"] == "Alarmstufe 2":
                            self.stage_levels[1] = float(station_data["data"][-1][1])
                        elif station_data["ts_name"] == "Alarmstufe 3":
                            self.stage_levels[2] = float(station_data["data"][-1][1])
                        elif station_data["ts_name"] == "Alarmstufe 4":
                            self.stage_levels[3] = float(station_data["data"][-1][1])
                LOGGER.debug("Stage levels : %s", self.stage_levels)
        except:
            self.stage_levels = [None] * 4
            LOGGER.debug("%s: No stage levels available", self.ident)

    def parse_ST(self):
        """Parse data for Sachsen-Anhalt."""
        if self.internal_url is None:
            self.level = None
            self.flow = None
            self.stage = None
            self.data_valid = False
            return

        last_update_str_w = None
        try:
            # Get data
            data = self.fetch_json(self.internal_url + "/W/week.json")
            # Parse data
            last_update_str_w = data[0]["data"][-1][0]
            self.level = float(data[0]["data"][-1][1])
            self.calc_stage()
        except:
            self.level = None
            self.stage = None
            LOGGER.debug("%s: No level data available", self.ident)

        last_update_str_q = None
        try:
            # Get data
            data = self.fetch_json(self.internal_url + "/Q/week.json")
            # Parse data
            last_update_str_q = data[0]["data"][-1][0]
            self.flow = float(data[0]["data"][-1][1])
        except:
            self.flow = None
            LOGGER.debug("%s: No flow data available", self.ident)

        if self.level is not None:
            self.data_valid = True
            self.last_update = datetime.datetime.fromisoformat(last_update_str_w)
        elif self.level is not None:
            self.data_valid = True
            self.last_update = datetime.datetime.fromisoformat(last_update_str_q)
        else:
            self.data_valid = False
            LOGGER.error("An error occured while fetching data for %s", self.ident)

    def parse_init_TH(self):
        """Parse data for Thüringen."""
        try:
            # Get data
            soup = self.fetch_soup(
                "https://hnz.thueringen.de/hw-portal/thueringen.html"
            )
            table = soup.find_all("table", id="pegelTabelle")[0]
            tbody = table.find_all("tbody")[0]
            trs = tbody.find_all("tr")
            # Parse data
            for tr in trs:
                tds = tr.find_all("td")
                cnt = 0
                for td in tds:
                    if (cnt == 1) and (td.getText().strip() != self.ident[3:]):
                        break
                    if cnt == 1:
                        links = td.find_all("a")
                        self.url = "https://hnz.thueringen.de" + links[0]["href"]
                    elif cnt == 2:
                        self.name = td.getText().strip()
                    elif cnt == 3:
                        self.name += " / " + td.getText().strip()
                        break
                    cnt += 1
                if cnt == 3:
                    break
        except Exception as e:
            LOGGER.error(
                "An error occured while fetching init data for %s: %s", self.ident, e
            )

    def parse_TH(self):
        """Parse data for Thüringen."""
        self.level = None
        self.flow = None
        self.stage = None
        try:
            # Get data
            soup = self.fetch_soup(
                "https://hnz.thueringen.de/hw-portal/thueringen.html"
            )
            table = soup.find_all("table", id="pegelTabelle")[0]
            tbody = table.find_all("tbody")[0]
            trs = tbody.find_all("tr")
            # Parse data
            last_update_str = None
            for tr in trs:
                tds = tr.find_all("td")
                cnt = 0
                for td in tds:
                    if (cnt == 1) and (td.getText().strip() != self.ident[3:]):
                        break
                    if cnt == 7:
                        last_update_str = td.getText().strip()
                    elif cnt == 8:
                        self.level = float(td.getText().strip().replace(",", "."))
                    elif cnt == 10:
                        self.flow = float(td.getText().strip().replace(",", "."))
                        break
                    cnt += 1
                if cnt == 10:
                    break
            if last_update_str is not None:
                self.last_update = datetime.datetime.strptime(
                    last_update_str, "%d.%m.%Y %H:%M"
                )
                self.data_valid = True
            else:
                self.last_update = None
                self.data_valid = False
        except Exception as e:
            self.data_valid = False
            LOGGER.error(
                "An error occured while fetching data for %s: %s", self.ident, e
            )

    def parse_init(self):
        """Init data."""
        if self.ident[0:3] == "BB_":
            self.parse_init_BB()
        elif self.ident[0:3] == "BE_":
            self.parse_init_BE()
        elif self.ident[0:3] == "BW_":
            self.parse_init_BW()
        elif self.ident[0:3] == "BY_":
            self.parse_init_BY()
        elif self.ident[0:3] == "HB_":
            self.parse_init_HB()
        elif self.ident[0:3] == "HE_":
            self.parse_init_HE()
        elif self.ident[0:3] == "HH_":
            self.parse_init_HH()
        elif self.ident[0:3] == "MV_":
            self.parse_init_MV()
        elif self.ident[0:3] == "NI_":
            self.parse_init_NI()
        elif self.ident[0:3] == "NW_":
            self.parse_init_NW()
        elif self.ident[0:3] == "RP_":
            self.parse_init_RP()
        elif self.ident[0:3] == "SH_":
            self.parse_init_SH()
        elif self.ident[0:3] == "SL_":
            self.parse_init_SL()
        elif self.ident[0:3] == "SN_":
            self.parse_init_SN()
        elif self.ident[0:3] == "ST_":
            self.parse_init_ST()
        elif self.ident[0:3] == "TH_":
            self.parse_init_TH()
        LOGGER.debug("Parse init API - %s", self.ident)

    def update(self):
        """Update data."""
        if self.ident[0:3] == "BB_":
            self.parse_BB()
        elif self.ident[0:3] == "BE_":
            self.parse_BE()
        elif self.ident[0:3] == "BW_":
            self.parse_BW()
        elif self.ident[0:3] == "BY_":
            self.parse_BY()
        elif self.ident[0:3] == "HB_":
            self.parse_HB()
        elif self.ident[0:3] == "HE_":
            self.parse_HE()
        elif self.ident[0:3] == "HH_":
            self.parse_HH()
        elif self.ident[0:3] == "MV_":
            self.parse_MV()
        elif self.ident[0:3] == "NI_":
            self.parse_NI()
        elif self.ident[0:3] == "NW_":
            self.parse_NW()
        elif self.ident[0:3] == "RP_":
            self.parse_RP()
        elif self.ident[0:3] == "SH_":
            self.parse_SH()
        elif self.ident[0:3] == "SL_":
            self.parse_SL()
        elif self.ident[0:3] == "SN_":
            self.parse_SN()
        elif self.ident[0:3] == "ST_":
            self.parse_ST()
        elif self.ident[0:3] == "TH_":
            self.parse_TH()
        LOGGER.debug("Update API - %s", self.ident)
