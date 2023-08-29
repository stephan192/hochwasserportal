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
CONF_LEVEL: Final = "level"
CONF_STAGE: Final = "stage"
CONF_FLOW: Final = "flow"

ATTR_DATA_PROVIDERS: Final[dict[str, str]] = {
    "BB": "https://pegelportal.brandenburg.de",
    "BE": "https://wasserportal.berlin.de",
    "BW": "https://www.hvz.baden-wuerttemberg.de",
    "BY": "https://www.hnd.bayern.de",
    "HB": "https://geoportale.dp.dsecurecloud.de/pegelbremen",
    "HE": "https://www.hochwasser-hessen.de",
    "HH": "https://www.wabiha.de/karte.html",
    "MV": "https://pegelportal-mv.de",
    "NI": "https://www.pegelonline.nlwkn.niedersachsen.de",
    "NW": "https://www.hochwasserportal.nrw.de",
    "RP": "https://hochwasser.rlp.de",
    "SH": "https://hsi-sh.de",
    "SL": "https://www.saarland.de/mukmav/DE/portale/wasser/informationen/hochwassermeldedienst/wasserstaende_warnlage/wasserstaende_warnlage_node.html",
    "SN": "https://www.umwelt.sachsen.de/umwelt/infosysteme/hwims/portal/web/wasserstand-uebersicht",
    "ST": "https://hochwasservorhersage.sachsen-anhalt.de",
    "TH": "https://hnz.thueringen.de/hw-portal",
}
ATTR_LAST_UPDATE: Final = "last_update"
ATTR_URL: Final = "url"
ATTR_HINT: Final = "hint"

LEVEL_SENSOR: Final = "level"
STAGE_SENSOR: Final = "stage"
FLOW_SENSOR: Final = "flow"

DEFAULT_SCAN_INTERVAL: Final = timedelta(minutes=15)

PLATFORMS: Final[list[Platform]] = [Platform.SENSOR]
