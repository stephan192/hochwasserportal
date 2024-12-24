"""Config flow for the hochwasserportal integration."""

from __future__ import annotations

from typing import Any

from lhpapi import HochwasserPortalAPI, LHPError, get_all_stations
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import CONF_ADD_UNAVAILABLE, CONF_PEGEL_IDENTIFIER, DOMAIN, LOGGER


class HochwasserPortalConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the config flow for the hochwasserportal integration."""

    VERSION = 1
    MINOR_VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict = {}

        if user_input is not None:
            pegel_identifier = user_input[CONF_PEGEL_IDENTIFIER]

            # Validate pegel identifier using the API
            try:
                api = await self.hass.async_add_executor_job(
                    HochwasserPortalAPI, pegel_identifier
                )
                LOGGER.debug(
                    "%s (%s): Successfully added!",
                    api.ident,
                    api.name,
                )
            except LHPError as err:
                LOGGER.exception("Setup of %s failed: %s", pegel_identifier, err)
                errors["base"] = "invalid_identifier"

            if not errors:
                # Set the unique ID for this config entry.
                await self.async_set_unique_id(f"{DOMAIN}_{pegel_identifier.lower()}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=f"{api.name}", data=user_input)

        stations_dict = await self.hass.async_add_executor_job(get_all_stations)
        LOGGER.debug(
            "%i stations found on Github",
            len(stations_dict),
        )
        stations = [SelectOptionDict(value="---", label="")]
        stations.extend(
            SelectOptionDict(value=k, label=f"{v} ({k})")
            for k, v in stations_dict.items()
        )
        return self.async_show_form(
            step_id="user",
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PEGEL_IDENTIFIER): SelectSelector(
                        SelectSelectorConfig(
                            options=stations,
                            mode=SelectSelectorMode.DROPDOWN,
                            sort=True,
                            custom_value=True,
                        )
                    ),
                    vol.Required(CONF_ADD_UNAVAILABLE, default=False): cv.boolean,
                }
            ),
        )
