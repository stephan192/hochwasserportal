"""Data coordinator for the hochwasserportal integration."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .lhp_api import HochwasserPortalAPI
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, LOGGER


class HochwasserPortalCoordinator(DataUpdateCoordinator[None]):
    """Custom coordinator for the hochwasserportal integration."""

    def __init__(self, hass: HomeAssistant, api: HochwasserPortalAPI) -> None:
        """Initialize the hochwasserportal coordinator."""
        super().__init__(
            hass, LOGGER, name=DOMAIN, update_interval=DEFAULT_SCAN_INTERVAL
        )

        self.api = api
        LOGGER.debug(
            "%s (%s): stage_levels=%s",
            self.api.ident,
            self.api.name,
            self.api.stage_levels,
        )
        LOGGER.debug("%s (%s): url=%s", self.api.ident, self.api.name, self.api.url)
        LOGGER.debug(
            "%s (%s): internal_url=%s",
            self.api.ident,
            self.api.name,
            self.api.internal_url,
        )
        if self.api.err_msg is not None:
            LOGGER.error("%s (%s): %s", self.api.ident, self.api.name, self.api.err_msg)
            LOGGER.error("%s (%s): Init failed!", self.api.ident, self.api.name)
        else:
            LOGGER.debug("%s (%s): Init done!", self.api.ident, self.api.name)

    async def _async_update_data(self) -> None:
        """Get the latest data from the hochwasserportal API."""
        await self.hass.async_add_executor_job(self.api.update)
        LOGGER.debug(
            "%s (%s): level=%s, stage=%s, flow=%s, last_update=%s",
            self.api.ident,
            self.api.name,
            self.api.level,
            self.api.stage,
            self.api.flow,
            self.api.last_update,
        )
        if self.api.err_msg is not None:
            LOGGER.error("%s (%s): %s", self.api.ident, self.api.name, self.api.err_msg)
            LOGGER.error("%s (%s): Update failed!", self.api.ident, self.api.name)
        else:
            LOGGER.debug("%s (%s): Update done!", self.api.ident, self.api.name)
