"""Constants for the Länderübergreifendes Hochwasser Portal integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Final

from homeassistant.const import Platform

LOGGER = logging.getLogger(__package__)

DOMAIN: Final = "hochwasserportal"

CONF_PEGEL_IDENTIFIER: Final = "pegel_identifier"
CONF_PEGEL: Final = "pegel"
CONF_LEVEL = "level"
CONF_STAGE = "stage"
CONF_FLOW = "flow"

ATTRIBUTION: Final = "Data provided by https://www.hochwasserzentralen.de"
ATTR_LAST_UPDATE: Final = "last_update"
ATTR_URL: Final = "url"
ATTR_INFO: Final = "info"
ATTR_HINT: Final = "hint"

LEVEL_SENSOR: Final = "level"
STAGE_SENSOR: Final = "stage"
FLOW_SENSOR: Final = "flow"

API_TIMEOUT: Final = 10
DEFAULT_SCAN_INTERVAL: Final = timedelta(minutes=15)

PLATFORMS: Final[list[Platform]] = [Platform.SENSOR]
