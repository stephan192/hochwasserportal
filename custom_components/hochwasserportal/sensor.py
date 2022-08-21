"""Platform for sensor integration."""
from __future__ import annotations
from datetime import timedelta
import logging
import datetime
import voluptuous as vol
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import ATTR_ATTRIBUTION, LENGTH_CENTIMETERS
import homeassistant.helpers.config_validation as cv
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import Throttle

import requests

_LOGGER = logging.getLogger(__name__)

CONF_PEGEL = "pegel"
CONF_LEVEL = "level"
CONF_STAGE = "stage"
CONF_FLOW = "flow"

ATTRIBUTION = "Data provided by https://www.hochwasserzentralen.de"
ATTR_LAST_UPDATE = "last_update"
ATTR_URL = "url"
ATTR_INFO = "info"
ATTR_HINT = "hint"

SCAN_INTERVAL = timedelta(minutes=15)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_PEGEL): cv.string,
        vol.Optional(CONF_LEVEL, default=True): cv.boolean,
        vol.Optional(CONF_STAGE, default=True): cv.boolean,
        vol.Optional(CONF_FLOW, default=True): cv.boolean,
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    api = HochwasserPortalAPI(config.get(CONF_PEGEL))
    if api.data is not None:
        if config.get(CONF_LEVEL) is True:
            add_entities([HochwasserPortalLevelSensor(api)])
        if config.get(CONF_STAGE) is True:
            add_entities([HochwasserPortalStageSensor(api)])
        if config.get(CONF_FLOW) is True:
            add_entities([HochwasserPortalFlowSensor(api)])


class HochwasserPortalLevelSensor(SensorEntity):
    """Representation of the level sensor."""
    _attr_native_unit_of_measurement = LENGTH_CENTIMETERS
    _attr_device_class = None
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_extra_state_attributes = {ATTR_ATTRIBUTION: ATTRIBUTION}
    _attr_icon = "mdi:waves"

    def __init__(self, api):
        """Initialize the sensor."""
        self._api = api
        self._attr_name = self._api.name + " Level"
        self._attr_unique_id = "hochwasserportal_" + self._api.ident.lower() + "_level"
        self.update()

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        self._api.update()
        if self._api.level is not None:
            self._attr_available = True
            self._attr_native_value = self._api.level
        else:
            self._attr_available = False
        self._attr_extra_state_attributes = {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            ATTR_LAST_UPDATE: self._api.last_update,
            ATTR_URL: self._api.url,
            ATTR_INFO: self._api.info,
            ATTR_HINT: self._api.hint,
        }
        _LOGGER.debug("Update %s", self.name)


class HochwasserPortalStageSensor(SensorEntity):
    """Representation of the stage sensor."""
    _attr_native_unit_of_measurement = None
    _attr_device_class = None
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_extra_state_attributes = {ATTR_ATTRIBUTION: ATTRIBUTION}
    _attr_icon = "mdi:waves-arrow-up"

    def __init__(self, api):
        """Initialize the sensor."""
        self._api = api
        self._attr_name = self._api.name + " Stage"
        self._attr_unique_id = "hochwasserportal_" + self._api.ident.lower() + "_stage"
        self.update()

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        self._api.update()
        if self._api.stage is not None:
            self._attr_available = True
            self._attr_native_value = self._api.stage
        else:
            self._attr_available = False
        self._attr_extra_state_attributes = {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            ATTR_LAST_UPDATE: self._api.last_update,
            ATTR_URL: self._api.url,
            ATTR_INFO: self._api.info,
            ATTR_HINT: self._api.hint,
        }
        _LOGGER.debug("Update %s", self.name)


class HochwasserPortalFlowSensor(SensorEntity):
    """Representation of the flow Sensor."""
    _attr_native_unit_of_measurement = "m³/s"
    _attr_device_class = None
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_extra_state_attributes = {ATTR_ATTRIBUTION: ATTRIBUTION}
    _attr_icon = "mdi:waves-arrow-right"

    def __init__(self, api):
        """Initialize the sensor."""
        self._api = api
        self._attr_name = self._api.name + " Flow"
        self._attr_unique_id = "hochwasserportal_" + self._api.ident.lower() + "_flow"
        self.update()

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        self._api.update()
        if self._api.flow is not None:
            self._attr_available = True
            self._attr_native_value = self._api.flow
        else:
            self._attr_available = False
        self._attr_extra_state_attributes = {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            ATTR_LAST_UPDATE: self._api.last_update,
            ATTR_URL: self._api.url,
            ATTR_INFO: self._api.info,
            ATTR_HINT: self._api.hint,
        }
        _LOGGER.debug("Update %s", self.name)


class HochwasserPortalAPI:
    """API to retrieve the data."""

    def __init__(self, ident):
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
            _LOGGER.debug("Init API - %s (%s) - Done!", self.ident, self.name)
        else:
            _LOGGER.error("Init API - %s - Failed!", self.ident)

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

    @Throttle(SCAN_INTERVAL)
    def update(self):
        """Fetch new data from the API."""
        try:
            resp = requests.post(
                "https://www.hochwasserzentralen.de/webservices/get_infospegel.php",
                data={"pgnr": self.ident},
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
        _LOGGER.debug("Update API - %s", self.ident)
