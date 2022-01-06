"""Degree Days integration."""
from datetime import timedelta
import datetime
import logging

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
    CONF_GAS_SENSOR,
    CONF_GAS_USE_OTHER,
    DEFAULT_HEATING_LIMIT,
    DEFAULT_INDOOR_TEMP,
    DEFAULT_WEATHER_STATION,
    DEFAULT_STARTDAY,
    DEFAULT_STARTMONTH,
    DEFAULT_GAS_SENSOR,
    DEFAULT_GAS_USE_OTHER,
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

        """Populate default options."""
        if not self.config_entry.options:
            data = dict(self.config_entry.data)
            options = {
                CONF_WEATHER_STATION: data.pop(CONF_WEATHER_STATION, DEFAULT_WEATHER_STATION),
                CONF_INDOOR_TEMP: data.pop(CONF_INDOOR_TEMP, DEFAULT_INDOOR_TEMP),
                CONF_HEATING_LIMIT: data.pop(CONF_HEATING_LIMIT, DEFAULT_HEATING_LIMIT),
                CONF_STARTDAY: data.pop(CONF_STARTDAY, DEFAULT_STARTDAY),
                CONF_STARTMONTH: data.pop(CONF_STARTMONTH, DEFAULT_STARTMONTH),
                CONF_GAS_SENSOR: data.pop(CONF_GAS_SENSOR, DEFAULT_GAS_SENSOR),
                CONF_GAS_USE_OTHER: data.pop(CONF_GAS_USE_OTHER, DEFAULT_GAS_USE_OTHER),
            }

            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=data,
                options=options
            )

        self.weather_station = entry.options[CONF_WEATHER_STATION]
        self.indoor_temp = entry.options[CONF_INDOOR_TEMP]
        self.heating_limit = entry.options[CONF_HEATING_LIMIT]
        self.start_day = entry.options[CONF_STARTDAY]
        self.start_month = entry.options[CONF_STARTMONTH]
        self.gas_sensor = entry.options[CONF_GAS_SENSOR]
        self.gas_use_other = entry.options[CONF_GAS_USE_OTHER]
        self.unique_id = entry.entry_id
        self.name = entry.title
        d = datetime.datetime.strptime(
            "2022" + self.start_month + str(self.start_day), "%Y%B%d"
        )
        self.startdate = d.strftime("%Y%m%d")

    async def _async_update_data(self):
        """Update the data from the KNMI device."""
        
        # Get gas consumption state
        try:
            self.gas_sensor_state = self.hass.states.get(self.gas_sensor)
            self.gas_consumption = float(self.gas_sensor_state.state)
        except AttributeError as err:
            self.gas_consumption = 0
        try:
            data = await self.hass.async_add_executor_job(
                KNMI,
                self.startdate,
                self.weather_station,
                self.indoor_temp,
                self.heating_limit,
                self.gas_consumption,
                self.gas_use_other
            )

        except (OSError, Timeout, HTTPError) as err:
            raise update_coordinator.UpdateFailed(err)

        self.logger.debug(
            "Connection to KNMI successful. Total sum degree days this year %s",
            data,
        )

        return data
