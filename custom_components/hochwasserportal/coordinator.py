"""Data coordinator for the hochwasserportal integration."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, LOGGER
from .lhp_api import HochwasserPortalAPI, LHPError


class HochwasserPortalCoordinator(DataUpdateCoordinator[None]):
    """Custom coordinator for the hochwasserportal integration."""

    def __init__(self, hass: HomeAssistant, api: HochwasserPortalAPI) -> None:
        """Initialize the hochwasserportal coordinator."""
        super().__init__(
            hass, LOGGER, name=DOMAIN, update_interval=DEFAULT_SCAN_INTERVAL
        )

        self.api = api
        LOGGER.debug("%s", repr(self.api))

    async def _async_update_data(self) -> None:
        """Get the latest data from the hochwasserportal API."""
        try:
            await self.hass.async_add_executor_job(self.api.update)
            LOGGER.debug("%s", repr(self.api))
        except LHPError as err:
            LOGGER.exception("Update of %s failed: %s", self.api.ident, err)
            return False
