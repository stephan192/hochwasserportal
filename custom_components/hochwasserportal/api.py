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
        self.info = None
        self.ni_sta_id = None
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

    def fetch_soup(self, url):
        """Fetch data via soup."""
        try:
            response = requests.get(url, timeout=API_TIMEOUT)
            # Override encoding by real educated guess (required for SH)
            response.encoding = response.apparent_encoding
            response.raise_for_status()
            soup = bs4.BeautifulSoup(response.text, "lxml")
            return soup
        except:
            # Don't care about errors because in some cases the requested page doesn't exist
            return None

    def fetch_text(self, url):
        """Fetch data via text."""
        try:
            response = requests.get(url, timeout=API_TIMEOUT)
            # Override encoding by real educated guess (required for BW)
            response.encoding = response.apparent_encoding
            response.raise_for_status()
            return response.text
        except:
            # Don't care about errors because in some cases the requested page doesn't exist
            return None

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
        pass

    def parse_BB(self):
        """Parse data for Brandenburg."""
        pass

    def parse_init_BE(self):
        """Parse data for Berlin."""
        pass

    def parse_BE(self):
        """Parse data for Berlin."""
        pass

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
                    if data[30] > 0:
                        self.stage_levels[0] = float(data[30])
                    if data[31] > 0:
                        self.stage_levels[1] = float(data[31])
                    if data[32] > 0:
                        self.stage_levels[2] = float(data[32])
                    if data[33] > 0:
                        self.stage_levels[3] = float(data[33])
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
        pass

    def parse_HB(self):
        """Parse data for Bremen."""
        pass

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
        pass

    def parse_HH(self):
        """Parse data for Hamburg."""
        pass

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
            self.ni_sta_id = None
            self.url = "https://www.pegelonline.nlwkn.niedersachsen.de"
            for entry in data["getStammdatenResult"]:
                if entry["STA_Nummer"] == self.ident[3:]:
                    self.name = entry["Name"] + " / " + entry["GewaesserName"]
                    self.ni_sta_id = str(entry["STA_ID"])
                    self.url += "/Pegel/Karte/Binnenpegel/ID/" + self.ni_sta_id
                    break
        except Exception as e:
            LOGGER.error(
                "An error occured while fetching init data for %s: %s", self.ident, e
            )

    def parse_NI(self):
        """Parse data for Niedersachsen."""
        if self.ni_sta_id is None:
            return

        try:
            # Get data
            data = self.fetch_json(
                "https://bis.azure-api.net/PegelonlinePublic/REST/stammdaten/stationen/"
                + self.ni_sta_id
                + "?key=9dc05f4e3b4a43a9988d747825b39f43"
            )
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
