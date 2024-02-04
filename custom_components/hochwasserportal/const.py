"""Constants for the Länderübergreifendes Hochwasser Portal integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Final

from homeassistant.const import Platform

LOGGER = logging.getLogger(__package__)

DOMAIN: Final = "hochwasserportal"

CONF_PEGEL_IDENTIFIER: Final = "pegel_identifier"
CONF_ADD_UNAVAILABLE: Final = "add_unavailable"

ATTR_DATA_PROVIDERS: Final[dict[str, str]] = {
    "BB": "LfU Brandenburg",
    "BE": "SenMVKU Berlin",
    "BW": "LUBW Baden-Württemberg",
    "BY": "LfU Bayern",
    "HB": "SUKW Bremen",
    "HE": "HLNUG",
    "HH": "LSBG Hamburg",
    "MV": "LUNG Mecklenburg-Vorpommern",
    "NI": "NLWKN",
    "NW": "LANUV Nordrhein-Westfalen",
    "RP": "Luf Rheinland-Pfalz",
    "SH": "Luf Schleswig-Holstein",
    "SL": "LUA Saarland",
    "SN": "LfULG Sachsen",
    "ST": "Land Sachsen-Anhalt",
    "TH": "TLUBN",
}
ATTR_LAST_UPDATE: Final = "last_update"
ATTR_URL: Final = "url"
ATTR_HINT: Final = "hint"

LEVEL_SENSOR: Final = "level"
STAGE_SENSOR: Final = "stage"
FLOW_SENSOR: Final = "flow"

DEFAULT_SCAN_INTERVAL: Final = timedelta(minutes=15)

PLATFORMS: Final[list[Platform]] = [Platform.SENSOR]
