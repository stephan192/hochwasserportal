"""The Länderübergreifendes Hochwasser Portal API."""

from __future__ import annotations
from .const import API_TIMEOUT, LOGGER
import datetime
import requests


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
        self.update()
        if self.data is not None:
            if "PN" in self.data:
                self.name = self.data["PN"]
            if "GW" in self.data:
                self.name += " / " + self.data["GW"]
            LOGGER.debug("Init API - %s (%s) - Done!", self.ident, self.name)
        else:
            LOGGER.error("Init API - %s - Failed!", self.ident)

    def __bool__(self):
        """Return the data_valid attribute."""
        if self.data is not None:
            return True
        return False

    def parse_values(self):
        """Parse fetched data."""
        if "W" in self.data:
            try:
                if self.data["W"].find(" ") == -1:
                    self.level = None
                else:
                    if self.data["W"][self.data["W"].find(" ") + 1 :].lower() == "cm":
                        self.level = int(self.data["W"][0 : self.data["W"].find(" ")])
                    elif (
                        self.data["W"][self.data["W"].find(" ") + 1 :].lower() == "mnap"
                    ):
                        self.level = int(
                            float(
                                self.data["W"][0 : self.data["W"].find(" ")].replace(
                                    ",", "."
                                )
                            )
                            * 100.0
                        )
            except:  # pylint: disable=bare-except # noqa: E722
                self.level = None
        else:
            self.level = None
        if "Q" in self.data:
            try:
                if self.data["Q"].find(" ") == -1:
                    self.flow = None
                else:
                    self.flow = self.data["Q"][0 : self.data["Q"].find(" ")]
                    self.flow = float(self.flow.replace(",", "."))
            except:  # pylint: disable=bare-except # noqa: E722
                self.flow = None
        else:
            self.flow = None
        if "HW" in self.data:
            try:
                self.stage = int(self.data["HW"])
            except:  # pylint: disable=bare-except # noqa: E722
                self.stage = None
            if self.stage == -1:  # No data available
                self.stage = None
        else:
            self.stage = None
        if "URL_PEGEL" in self.data and self.data["URL_PEGEL"] != "":
            self.url = self.data["URL_PEGEL"]
        elif "URL_LAND" in self.data and self.data["URL_LAND"] != "":
            self.url = self.data["URL_LAND"]
        else:
            self.url = "https://www.hochwasserzentralen.de"
        if "HINT" in self.data:
            self.hint = self.data["HINT"]
        else:
            self.hint = None
        if "HW_TXT" in self.data:
            self.info = self.data["HW_TXT"]
        else:
            self.info = None

    def update(self):
        """Fetch new data from the API."""
        try:
            resp = requests.post(
                "https://www.hochwasserzentralen.de/webservices/get_infospegel.php",
                data={"pgnr": self.ident},
                timeout=API_TIMEOUT,
            )
            self.data = resp.json()
            if "PN" in self.data:
                if self.data["PN"] == "":
                    self.data = None
            else:
                self.data = None
        except:  # pylint: disable=bare-except # noqa: E722
            self.data = None
        if self.data is not None:
            self.parse_values()
        self.last_update = datetime.datetime.now(datetime.timezone.utc)
        LOGGER.debug("Update API - %s", self.ident)
