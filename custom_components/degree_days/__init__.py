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
    CONF_CONSUMPTION_SENSOR,
    CONF_DHW_CONSUMPTION,
    CONF_HEATPUMP,
    CONF_GAS_SENSOR,
    CONF_GAS_USE_OTHER,
    DEFAULT_HEATING_LIMIT,
    DEFAULT_INDOOR_TEMP,
    DEFAULT_WEATHER_STATION,
    DEFAULT_STARTDAY,
    DEFAULT_STARTMONTH,
    DEFAULT_CONSUMPTION_SENSOR,
    DEFAULT_DHW_CONSUMPTION,
    DEFAULT_HEATPUMP,
    DOMAIN
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry for graaddagen."""
    coordinator = DegreeDaysData(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

async def async_migrate_entry(hass, config_entry):
    """Migrate config entry to new version."""
    if config_entry.version <= 4:
        options = dict(config_entry.options)
        if CONF_HEATPUMP not in options:
            options[CONF_HEATPUMP] = DEFAULT_HEATPUMP

        if CONF_GAS_SENSOR in options:
            options[CONF_CONSUMPTION_SENSOR] = options[CONF_GAS_SENSOR]
            del options[CONF_GAS_SENSOR]

        if CONF_GAS_USE_OTHER in options:
            options[CONF_DHW_CONSUMPTION] = options[CONF_GAS_USE_OTHER]
            del options[CONF_GAS_USE_OTHER]

        config_entry.version = 5
        hass.config_entries.async_update_entry(config_entry, options=options)
        _LOGGER.error("Migrated config entry to version %d", config_entry.version)

    return True


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
                CONF_CONSUMPTION_SENSOR: data.pop(CONF_CONSUMPTION_SENSOR, DEFAULT_CONSUMPTION_SENSOR),
                CONF_DHW_CONSUMPTION: data.pop(CONF_DHW_CONSUMPTION, DEFAULT_CONSUMPTION_USE_OTHER),
                CONF_HEATPUMP: data.pop(CONF_HEATPUMP, DEFAULT_HEATPUMP),
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
        self.total_consumption_sensor = entry.options[CONF_CONSUMPTION_SENSOR]
        self.dwh_consumption = entry.options[CONF_DHW_CONSUMPTION]
        self.heatpump = entry.options[CONF_HEATPUMP]
        self.unique_id = entry.entry_id
        self.name = entry.title

        startdate = datetime.datetime.strptime(self.start_month + str(self.start_day), "%B%d")
        today = datetime.datetime.today()
        # define year of given start month and start day
        if today.month < startdate.month:
            year = today.year - 1
        elif today.month == startdate.month:
            if today.day < startdate.day:
                year = today.year - 1
            else:
                year = today.year
        else:
            year = today.year
        self.startdate = datetime.datetime.strptime(str(year) + self.start_month + str(self.start_day),
                                                    "%Y%B%d").strftime("%Y%m%d")

    async def _async_update_data(self):
        """Update the data from the KNMI device."""
        
        # Get consumption state
        try:
            self.total_consumption_sensor_state = self.hass.states.get(self.total_consumption_sensor)
            self.total_consumption = float(self.total_consumption_sensor_state.state)
        except AttributeError:
            self.total_consumption = 0
        try:
            data = await self.hass.async_add_executor_job(
                KNMI,
                self.startdate,
                self.weather_station,
                self.indoor_temp,
                self.heating_limit,
                self.total_consumption,
                self.dwh_consumption,
                self.heatpump
            )

        except (OSError, Timeout, HTTPError) as err:
            raise update_coordinator.UpdateFailed(err)

        self.logger.debug(
            "Connection to KNMI successful. Total sum degree days this year %s",
            data,
        )

        return data
