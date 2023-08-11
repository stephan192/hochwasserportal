"""Platform for sensor integration."""
from __future__ import annotations

from typing import Final

import voluptuous as vol

from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_PEGEL,
    CONF_LEVEL,
    CONF_STAGE,
    CONF_FLOW,
    ATTRIBUTION,
    ATTR_LAST_UPDATE,
    ATTR_URL,
    ATTR_INFO,
    ATTR_HINT,
    LEVEL_SENSOR,
    STAGE_SENSOR,
    FLOW_SENSOR,
    DOMAIN,
    LOGGER,
)
from .coordinator import HochwasserPortalCoordinator

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_PEGEL): cv.string,
        vol.Optional(CONF_LEVEL, default=True): cv.boolean,
        vol.Optional(CONF_STAGE, default=True): cv.boolean,
        vol.Optional(CONF_FLOW, default=True): cv.boolean,
    }
)

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=LEVEL_SENSOR,
        icon="mdi:waves",
        native_unit_of_measurement=UnitOfLength.CENTIMETERS,
    ),
    SensorEntityDescription(
        key=STAGE_SENSOR,
        icon="mdi:waves-arrow-up",
        native_unit_of_measurement=None,
    ),
    SensorEntityDescription(
        key=FLOW_SENSOR,
        icon="mdi:waves-arrow-right",
        native_unit_of_measurement="m³/s",
    ),
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Import the configurations from YAML to config flows."""
    # Show issue as long as the YAML configuration exists.
    async_create_issue(
        hass,
        DOMAIN,
        "deprecated_yaml",
        is_fixable=False,
        severity=IssueSeverity.WARNING,
        translation_key="deprecated_yaml",
    )

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=config
        )
    )


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up entities from config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            HochwasserPortalSensor(coordinator, entry, description)
            for description in SENSOR_TYPES
        ],
        True,
    )


class HochwasserPortalSensor(
    CoordinatorEntity[HochwasserPortalCoordinator], SensorEntity
):
    """Sensor representation."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: HochwasserPortalCoordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.api = coordinator.api
        self.entity_description = description
        self._attr_device_class = None
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._attr_icon = description.icon
        self._attr_name = f"{description.key.capitalize()}"
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)}, name=f"{entry.title}"
        )
        LOGGER.debug("Setting up sensor: %s", self._attr_name)
        LOGGER.debug("Unique id: %s", self._attr_unique_id)

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.entity_description.key == LEVEL_SENSOR:
            return self.api.level
        if self.entity_description.key == STAGE_SENSOR:
            return self.api.stage
        return self.api.flow

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        data = {}
        if self.api.last_update is not None:
            data[ATTR_LAST_UPDATE] = self.api.last_update
        if self.api.url is not None:
            data[ATTR_URL] = self.api.url
        if self.api.info is not None:
            data[ATTR_INFO] = self.api.info
        if self.api.hint is not None:
            data[ATTR_HINT] = self.api.hint
        return data

    @property
    def available(self) -> bool:
        """Could the device be accessed during the last update call."""
        if self.entity_description.key == LEVEL_SENSOR:
            if self.api.level is not None:
                return True
            return False
        if self.entity_description.key == STAGE_SENSOR:
            if self.api.stage is not None:
                return True
            return False
        if self.api.flow is not None:
            return True
        return False
