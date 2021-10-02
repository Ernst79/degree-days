"""Degree Days integration."""
from datetime import timedelta
import datetime
import logging
from urllib.parse import ParseResult, urlparse

from .knmi import KNMI
from requests.exceptions import HTTPError, Timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import update_coordinator

from .const import (
    CONF_HEATING_LIMIT,
    CONF_INDOOR_TEMP,
    CONF_WEATHER_STATION,
    CONF_STARTDAY,
    CONF_STARTMONTH,
    CONF_GAS_CONSUMPTION,
    DOMAIN
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry for graaddagen."""
    coordinator = DegreeDaysData(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


class DegreeDaysData(update_coordinator.DataUpdateCoordinator):
    """Get and update the latest data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the data object."""
        super().__init__(
            hass, _LOGGER, name="Degree Days", update_interval=timedelta(seconds=600)
        )

        self.heating_limit = entry.data[CONF_HEATING_LIMIT]
        self.indoor_temp = entry.data[CONF_INDOOR_TEMP]
        self.weather_station = entry.data[CONF_WEATHER_STATION]
        self.gas_consumption = entry.data[CONF_GAS_CONSUMPTION]
        self.start_day = entry.data[CONF_STARTDAY]
        self.start_month = entry.data[CONF_STARTMONTH]
        self.unique_id = entry.entry_id
        self.name = entry.title
        
        d = datetime.datetime.strptime(
            "2021" + self.start_month + str(self.start_day), "%Y%B%d"
        )
        self.startdate = d.strftime("%Y%m%d")

    async def _async_update_data(self):
        """Update the data from the KNMI device."""
        try:
            data = await self.hass.async_add_executor_job(
                KNMI,
                self.startdate,
                self.weather_station,
                self.indoor_temp,
                self.heating_limit,
                self.gas_consumption
            )

        except (OSError, Timeout, HTTPError) as err:
            raise update_coordinator.UpdateFailed(err)

        self.logger.debug(
            "Connection to KNMI successful. Total sum degree days this year %s",
            data,
        )

        return data
