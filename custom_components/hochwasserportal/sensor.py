"""Platform for sensor integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_DATA_PROVIDERS,
    ATTR_HINT,
    ATTR_LAST_UPDATE,
    ATTR_URL,
    DOMAIN,
    FLOW_SENSOR,
    LEVEL_SENSOR,
    LOGGER,
    STAGE_SENSOR,
)
from .coordinator import HochwasserPortalCoordinator

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=LEVEL_SENSOR,
        translation_key=LEVEL_SENSOR,
        icon="mdi:waves",
        native_unit_of_measurement=UnitOfLength.CENTIMETERS,
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=STAGE_SENSOR,
        translation_key=STAGE_SENSOR,
        icon="mdi:waves-arrow-up",
        native_unit_of_measurement=None,
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=FLOW_SENSOR,
        translation_key=FLOW_SENSOR,
        icon="mdi:waves-arrow-right",
        native_unit_of_measurement="m³/s",
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
    ),
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
        ]
    )


class HochwasserPortalSensor(
    CoordinatorEntity[HochwasserPortalCoordinator], SensorEntity
):
    """Sensor representation."""

    _attr_has_entity_name = True

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
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)}, name=f"{entry.title}"
        )
        self._attr_attribution = (
            f"Data provided by {ATTR_DATA_PROVIDERS[self.api.ident[:2]]}"
        )
        LOGGER.debug("Setting up sensor: %s", self._attr_unique_id)

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
