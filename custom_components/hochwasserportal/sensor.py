"""Platform for sensor integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from lhpapi import HochwasserPortalAPI

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
    CONF_ADD_UNAVAILABLE,
    DOMAIN,
    FLOW_SENSOR,
    LEVEL_SENSOR,
    LOGGER,
    STAGE_SENSOR,
)
from .coordinator import HochwasserPortalCoordinator


@dataclass(frozen=True, kw_only=True)
class HochwasserPortalSensorEntityDescription(SensorEntityDescription):
    """Describes HochwasserPortal sensor entity."""

    value_fn: Callable[[HochwasserPortalAPI], int | float | None]
    available_fn: Callable[[HochwasserPortalAPI], bool]


SENSOR_TYPES: tuple[HochwasserPortalSensorEntityDescription, ...] = (
    HochwasserPortalSensorEntityDescription(
        key=LEVEL_SENSOR,
        translation_key=LEVEL_SENSOR,
        icon="mdi:waves",
        native_unit_of_measurement=UnitOfLength.CENTIMETERS,
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda api: api.level,
        available_fn=lambda api: api.level is not None,
    ),
    HochwasserPortalSensorEntityDescription(
        key=STAGE_SENSOR,
        translation_key=STAGE_SENSOR,
        icon="mdi:waves-arrow-up",
        native_unit_of_measurement=None,
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda api: api.stage,
        available_fn=lambda api: api.stage is not None,
    ),
    HochwasserPortalSensorEntityDescription(
        key=FLOW_SENSOR,
        translation_key=FLOW_SENSOR,
        icon="mdi:waves-arrow-right",
        native_unit_of_measurement="m³/s",
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda api: api.flow,
        available_fn=lambda api: api.flow is not None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up entities from config entry."""
    coordinator: HochwasserPortalCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            HochwasserPortalSensor(coordinator, entry, description)
            for description in SENSOR_TYPES
            if description.available_fn(coordinator.api)
            or entry.data.get(CONF_ADD_UNAVAILABLE, False)
        ]
    )


class HochwasserPortalSensor(
    CoordinatorEntity[HochwasserPortalCoordinator], SensorEntity
):
    """Sensor representation."""

    entity_description: HochwasserPortalSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HochwasserPortalCoordinator,
        entry: ConfigEntry,
        description: HochwasserPortalSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.api = coordinator.api
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"{entry.title}",
            configuration_url=self.api.url,
            manufacturer=f"{ATTR_DATA_PROVIDERS[self.api.ident[:2]]}",
            model=f"{self.api.ident}",
        )
        self._attr_attribution = (
            f"Data provided by {ATTR_DATA_PROVIDERS[self.api.ident[:2]]}"
        )
        LOGGER.debug("Setting up sensor: %s", self._attr_unique_id)

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.api)

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
        if bool(data):
            return data
        return None

    @property
    def available(self) -> bool:
        """Could the device be accessed during the last update call."""
        return self.entity_description.available_fn(self.api)
