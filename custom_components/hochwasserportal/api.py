"""The Länderübergreifendes Hochwasser Portal API."""

from __future__ import annotations
from .const import API_TIMEOUT, LOGGER
import datetime
import requests
import bs4


class HochwasserPortalAPI:
    """API to retrieve the data."""

    def __init__(self, ident) -> None:
        """Initialize the API."""
        self.ident = ident
        self.name = None
        self.level = None
        self.stage = None
        self.flow = None
        self.url = None
        self.hint = None
        self.info = None
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
        try:
            response = requests.get(url, timeout=API_TIMEOUT)
            response.raise_for_status()
            json_data = response.json()
            return json_data
        except requests.exceptions.RequestException as e:
            LOGGER.error("An error occurred while fetching the JSON: %s", e)
            return None
        except ValueError as e:
            LOGGER.error("Error parsing JSON data: %s", e)
            return None

    def fetch_soup(self, url):
        try:
            response = requests.get(url, timeout=API_TIMEOUT)
            # Override encoding by real educated guess (required for SH)
            response.encoding = response.apparent_encoding
            response.raise_for_status()
            soup = bs4.BeautifulSoup(response.text, "lxml")
            return soup
        except requests.exceptions.RequestException as e:
            LOGGER.error("An error occurred while fetching the LXML: %s", e)
            return None
        except XMLSyntaxError as e:
            LOGGER.error("Error parsing LXML data: %s", e)
            return None

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
        pass

    def parse_BW(self):
        """Parse data for Baden-Württemberg."""
        pass

    def parse_init_BY(self):
        """Parse data for Bayern."""
        try:
            # Get data
            soup = self.fetch_soup(
                "https://www.hnd.bayern.de/pegel"
            )
            img_id = "p" + self.ident[3:]
            imgs = soup.find_all("img", id=img_id)
            data = imgs[0]
            # Parse data
            self.name = data.get("data-name")
            if len(data.get("data-zeile2")) > 0:
                self.name += " / " + data.get("data-zeile2")
            self.url = "https://www.hnd.bayern.de/pegel"
        except Exception as e:  # pylint: disable=bare-except # noqa: E722
            self.data_valid = False
            LOGGER.error("An error occured while fetching data for %s: %s", self.ident, e)

    def parse_BY(self):
        """Parse data for Bayern."""
        self.level = None
        self.flow = None
        self.stage = None
        try:
            # Get data
            soup = self.fetch_soup(
                "https://www.hnd.bayern.de/pegel"
            )
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
            self.data_valid = True
        except Exception as e:  # pylint: disable=bare-except # noqa: E722
            self.data_valid = False
            LOGGER.error("An error occured while fetching data for %s: %s", self.ident, e)
        self.last_update = datetime.datetime.now(datetime.timezone.utc)

    def parse_init_HB(self):
        """Parse data for Bremen."""
        pass

    def parse_HB(self):
        """Parse data for Bremen."""
        pass

    def parse_init_HE(self):
        """Parse data for Hessen."""
        pass

    def parse_HE(self):
        """Parse data for Hessen."""
        pass

    def parse_init_HH(self):
        """Parse data for Hamburg."""
        pass

    def parse_HH(self):
        """Parse data for Hamburg."""
        pass

    def parse_init_MV(self):
        """Parse data for Mecklenburg-Vorpommern."""
        pass

    def parse_MV(self):
        """Parse data for Mecklenburg-Vorpommern."""
        pass

    def parse_init_NI(self):
        """Parse data for Niedersachsen."""
        pass

    def parse_NI(self):
        """Parse data for Niedersachsen."""
        pass

    def parse_init_NW(self):
        """Parse data for Nordrhein-Westfalen."""
        try:
            # Get data
            data = self.fetch_json(
                "https://hochwasserportal.nrw/lanuv/data/internet/stations/100/"
                + self.ident[3:]
                + "/S/week.json"
            )
            # Parse data
            self.name = data[0]["station_name"] + " " + data[0]["WTO_OBJECT"]
            self.url = (
                "https://hochwasserportal.nrw/lanuv/data/internet/stations/100/"
                + self.ident[3:]
                + "/S/week.json"
            )
        except Exception as e: # pylint: disable=bare-except # noqa: E722
            self.data_valid = False
            LOGGER.error("An error occured while fetching data for %s: %s", self.ident, e)

    def parse_NW(self):
        """Parse data for Nordrhein-Westfalen."""
        self.level = None
        self.flow = None
        self.stage = None
        try:
            # Get data
            data = self.fetch_json(
                "https://hochwasserportal.nrw/lanuv/data/internet/stations/100/"
                + self.ident[3:]
                + "/S/week.json"
            )
            # Parse data
            if data[0]["data"][-1][1] > 0:
                self.level = data[0]["data"][-1][1]
            else:
                self.level = None
            self.hint = data[0]["AdminStatus"] + " / " + data[0]["AdminBemerkung"]
            self.data_valid = True
            # Extract the last update timestamp from the JSON data
            last_update_str = data[0]["data"][-1][0]
            # Convert the string timestamp to a datetime object
            self.last_update = datetime.datetime.fromisoformat(last_update_str)
        except Exception as e:  # pylint: disable=bare-except # noqa: E722
            self.data_valid = False
            self.last_update = datetime.datetime.now(datetime.timezone.utc)
            LOGGER.error("An error occured while fetching data for %s: %s", self.ident, e)            

    def parse_init_RP(self):
        """Parse data for Rheinland-Pfalz."""
        pass

    def parse_RP(self):
        """Parse data for Rheinland-Pfalz."""
        pass

    def parse_init_SH(self):
        """Parse data for Schleswig-Holstein."""
        try:
            # Get data
            soup = self.fetch_soup(
                "https://hsi-sh.de"
            )
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
            self.url = "https://hsi-sh.de"
        except Exception as e:  # pylint: disable=bare-except # noqa: E722
            self.data_valid = False
            LOGGER.error("An error occured while fetching data for %s: %s", self.ident, e)

    def parse_SH(self):
        """Parse data for Schleswig-Holstein."""
        self.level = None
        self.flow = None
        self.stage = None
        try:
            # Get data
            soup = self.fetch_soup(
                "https://hsi-sh.de"
            )
            search_string = "dialogheader-" + self.ident[3:]
            headings = soup.find_all("h1", id=search_string)
            # Parse data
            heading = headings[0]
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
                if (
                    element.name == "dd"
                    and element.attrs["class"][0] == "tooltip-content__q"
                ):
                    element_text = element.getText().split()
                    if element_text[1] == "m3/s":
                        self.flow = float(element_text[0].replace(",", "."))
            self.data_valid = True
        except Exception as e:  # pylint: disable=bare-except # noqa: E722
            self.data_valid = False
            LOGGER.error("An error occured while fetching data for %s: %s", self.ident, e)
        self.last_update = datetime.datetime.now(datetime.timezone.utc)

    def parse_init_SL(self):
        """Parse data for Saarland."""
        pass

    def parse_SL(self):
        """Parse data for Saarland."""
        pass

    def parse_init_SN(self):
        """Parse data for Sachsen."""
        pass

    def parse_SN(self):
        """Parse data for Sachsen."""
        pass

    def parse_init_ST(self):
        """Parse data for Sachsen-Anhalt."""
        pass

    def parse_ST(self):
        """Parse data for Sachsen-Anhalt."""
        pass

    def parse_init_TH(self):
        """Parse data for Thüringen."""
        pass

    def parse_TH(self):
        """Parse data for Thüringen."""
        pass

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
        elif self.ident[0:3] == "MW_":
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
        elif self.ident[0:3] == "MW_":
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
