"""Config flow for the hochwasserportal integration."""

from __future__ import annotations

from typing import Any

from .lhp_api import HochwasserPortalAPI
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import CONF_PEGEL_IDENTIFIER, CONF_PEGEL, DOMAIN, LOGGER


class HochwasserPortalConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the config flow for the hochwasserportal integration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict = {}

        if user_input is not None:
            pegel_identifier = user_input[CONF_PEGEL_IDENTIFIER]

            # Validate pegel identifier using the API
            pegel_title = repr(
                await self.hass.async_add_executor_job(
                    HochwasserPortalAPI, pegel_identifier
                )
            )
            if pegel_title == pegel_identifier:
                errors["base"] = "invalid_identifier"

            if not errors:
                # Set the unique ID for this config entry.
                await self.async_set_unique_id(f"{DOMAIN}_{pegel_identifier.lower()}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=pegel_title, data=user_input)

        return self.async_show_form(
            step_id="user",
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PEGEL_IDENTIFIER): cv.string,
                }
            ),
        )

    async def async_step_import(self, import_config: dict[str, Any]) -> FlowResult:
        """Import a config entry from configuration.yaml."""
        LOGGER.debug(
            "Starting import of sensor from configuration.yaml - %s", import_config
        )

        # Extract the necessary data for the setup.
        pegel_identifier = import_config[CONF_PEGEL]

        # Validate pegel identifier using the API
        pegel_title = repr(
            await self.hass.async_add_executor_job(
                HochwasserPortalAPI, pegel_identifier
            )
        )
        if pegel_title == pegel_identifier:
            return self.async_abort(reason="invalid_identifier")

        # Set the unique ID for this imported entry.
        await self.async_set_unique_id(f"{DOMAIN}_{pegel_identifier.lower()}")
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=pegel_title, data={CONF_PEGEL_IDENTIFIER: pegel_identifier}
        )
