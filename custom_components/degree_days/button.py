"""Button platform for degree days."""
from homeassistant.components.button import ButtonEntity

from . import DegreeDaysData
from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    """Add degree days buttons."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DegreeDaysRefreshButton(coordinator)])


class DegreeDaysRefreshButton(ButtonEntity):
    """Button to manually refresh degree days data."""

    def __init__(self, coordinator: DegreeDaysData) -> None:
        """Initialize the button."""
        self.coordinator = coordinator
        self._attr_name = "refresh degree days"
        self._attr_unique_id = f"{coordinator.unique_id}_refresh"
        self._attr_icon = "mdi:refresh"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_request_refresh()
