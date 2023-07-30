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
            resp = requests.get(
                "https://www.hnd.bayern.de/pegel",
                timeout=API_TIMEOUT,
            )
            soup = bs4.BeautifulSoup(resp.text, "lxml")
            img_id = "p" + self.ident[3:]
            imgs = soup.find_all("img", id=img_id)
            data = imgs[0]
            # Parse data
            self.name = data.get("data-name")
            if len(data.get("data-zeile2")) > 0:
                self.name += " / " + data.get("data-zeile2")
            self.url = "https://www.hnd.bayern.de/pegel"
        except:  # pylint: disable=bare-except # noqa: E722
            self.data_valid = False

    def parse_BY(self):
        """Parse data for Bayern."""
        self.level = None
        self.flow = None
        self.stage = None
        try:
            # Get data
            resp = requests.get(
                "https://www.hnd.bayern.de/pegel",
                timeout=API_TIMEOUT,
            )
            soup = bs4.BeautifulSoup(resp.text, "lxml")
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
        except:  # pylint: disable=bare-except # noqa: E722
            self.data_valid = False
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
            json_data = requests.get(
                "https://hochwasserportal.nrw/lanuv/data/internet/stations/100/" + self.ident[3:] + "/S/week.json",
                timeout=API_TIMEOUT,
            )            
            data = json_data.json()
            # Parse data
            self.name = data[0]['station_name']
            self.url = "https://hochwasserportal.nrw/lanuv/data/internet/stations/100/" + self.ident[3:] + "/S/week.json"
        except:  # pylint: disable=bare-except # noqa: E722
            self.data_valid = False

    def parse_NW(self):
        """Parse data for Nordrhein-Westfalen."""
        self.level = None
        self.flow = None
        self.stage = None
        try:
            # Get data
            json_data = requests.get(
                "https://hochwasserportal.nrw/lanuv/data/internet/stations/100/" + self.ident[3:] + "/S/week.json",
                timeout=API_TIMEOUT,
            )            
            data = json_data.json()
            # Parse data
            if data[0]['data'][-1][1] > 0:
                self.level = data[0]['data'][-1][1]
            else:
                self.level = None
            self.hint = data[0]['AdminStatus'] + " / " + data[0]['AdminBemerkung']
            self.data_valid = True
            # Extract the last update timestamp from the JSON data
            last_update_str = data[0]['data'][-1][0]
            # Convert the string timestamp to a datetime object
            self.last_update = datetime.datetime.fromisoformat(last_update_str)            
        except:  # pylint: disable=bare-except # noqa: E722
            self.data_valid = False
        self.last_update = datetime.datetime.now(datetime.timezone.utc)

    def parse_init_RP(self):
        """Parse data for Rheinland-Pfalz."""
        pass

    def parse_RP(self):
        """Parse data for Rheinland-Pfalz."""
        pass

    def parse_init_SH(self):
        """Parse data for Schleswig-Holstein."""
        pass

    def parse_SH(self):
        """Parse data for Schleswig-Holstein."""
        pass

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
