"""The Länderübergreifendes Hochwasser Portal integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .lhp_api import HochwasserPortalAPI
from .const import CONF_PEGEL_IDENTIFIER, DOMAIN, PLATFORMS
from .coordinator import HochwasserPortalCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    pegel_identifier: str = entry.data[CONF_PEGEL_IDENTIFIER]

    # Initialize the API and coordinator.
    api = await hass.async_add_executor_job(HochwasserPortalAPI, pegel_identifier)
    coordinator = HochwasserPortalCoordinator(hass, api)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
