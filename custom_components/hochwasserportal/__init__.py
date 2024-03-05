"""The Länderübergreifendes Hochwasser Portal integration."""

from __future__ import annotations

from lhpapi import HochwasserPortalAPI, LHPError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_ADD_UNAVAILABLE,
    CONF_PEGEL_IDENTIFIER,
    DOMAIN,
    LOGGER,
    PLATFORMS,
)
from .coordinator import HochwasserPortalCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    pegel_identifier: str = entry.data[CONF_PEGEL_IDENTIFIER]

    # Initialize the API and coordinator.
    try:
        api = await hass.async_add_executor_job(HochwasserPortalAPI, pegel_identifier)
        coordinator = HochwasserPortalCoordinator(hass, api)
    except LHPError as err:
        LOGGER.exception("Setup of %s failed: %s", pegel_identifier, err)
        return False

    # No need to refresh via the following line because api runs
    # update during init automatically
    # await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    LOGGER.debug(
        "Migrating %s from version %s.%s",
        config_entry.title,
        config_entry.version,
        config_entry.minor_version,
    )

    if config_entry.version > 1:
        # This means the user has downgraded from a future version
        return False

    if config_entry.version == 1:
        new = {**config_entry.data}
        if config_entry.minor_version < 2:
            new[CONF_ADD_UNAVAILABLE] = True  # Behaviour as in 1.1
            config_entry.minor_version = 2
            hass.config_entries.async_update_entry(config_entry, data=new)

    LOGGER.debug(
        "Migration of %s to version %s.%s successful",
        config_entry.title,
        config_entry.version,
        config_entry.minor_version,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
