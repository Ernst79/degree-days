"""Platform for degree days sensors."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers import update_coordinator
from homeassistant.helpers.entity import StateType

from . import DegreeDaysData
from .const import (
    DOMAIN,
    GAS_SENSOR_TYPES,
    HEATPUMP_SENSOR_TYPES,
    SENSOR_TYPES,
    DegreeDaysSensorEntityDescription
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Add degree days entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        DegreeDaysSensor(coordinator, description) for description in SENSOR_TYPES
    )
    if coordinator.heatpump:
        async_add_entities(
            DegreeDaysSensor(coordinator, description) for description in HEATPUMP_SENSOR_TYPES
        )
    else:
        async_add_entities(
            DegreeDaysSensor(coordinator, description) for description in GAS_SENSOR_TYPES
        )


class DegreeDaysSensor(update_coordinator.CoordinatorEntity, SensorEntity):
    """Representation of a Sensor."""

    entity_description: DegreeDaysSensorEntityDescription

    def __init__(
        self,
        coordinator: DegreeDaysData,
        description: DegreeDaysSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_name = f"{description.name}"
        self._attr_unique_id = f"{coordinator.unique_id}_{description.key}"

    @property
    def native_value(self) -> StateType:
        """Return the native sensor value."""
        state = getattr(self.coordinator.data, self.entity_description.key)
        return state
