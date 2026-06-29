"""Degree Days integration."""
import datetime
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers import update_coordinator
from requests.exceptions import HTTPError, Timeout

from .const import (CONF_CONSUMPTION_SENSOR, CONF_DHW_CONSUMPTION,
                    CONF_GAS_SENSOR, CONF_GAS_USE_OTHER, CONF_HEATING_LIMIT,
                    CONF_HEATPUMP, CONF_INDOOR_TEMP, CONF_STARTDAY,
                    CONF_STARTMONTH, CONF_WEATHER_STATION,
                    DEFAULT_CONSUMPTION_SENSOR, DEFAULT_DHW_CONSUMPTION,
                    DEFAULT_HEATING_LIMIT, DEFAULT_HEATPUMP,
                    DEFAULT_INDOOR_TEMP, DEFAULT_STARTDAY, DEFAULT_STARTMONTH,
                    DEFAULT_WEATHER_STATION, DOMAIN)
from .knmi import KNMI

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry for graaddagen."""
    coordinator = DegreeDaysData(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    if coordinator.total_consumption_sensor:
        entry.async_on_unload(
            async_track_state_change_event(
                hass,
                [coordinator.total_consumption_sensor],
                coordinator.async_handle_consumption_sensor_change,
            )
        )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_migrate_entry(hass, config_entry):
    """Migrate config entry to new version."""
    if config_entry.version == 1:
        options = dict(config_entry.options)
        if CONF_HEATPUMP not in options:
            options[CONF_HEATPUMP] = DEFAULT_HEATPUMP

        if CONF_GAS_SENSOR in options:
            options[CONF_CONSUMPTION_SENSOR] = options[CONF_GAS_SENSOR]
            del options[CONF_GAS_SENSOR]

        if CONF_GAS_USE_OTHER in options:
            options[CONF_DHW_CONSUMPTION] = options[CONF_GAS_USE_OTHER]
            del options[CONF_GAS_USE_OTHER]

        config_entry.version = 2
        hass.config_entries.async_update_entry(config_entry, options=options)
        _LOGGER.info("Migrated config entry to version %d", config_entry.version)

    return True


class DegreeDaysData(update_coordinator.DataUpdateCoordinator):
    """Get and update the latest data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the data object."""
        self.config_entry = entry
        super().__init__(
            hass,
            _LOGGER,
            name="Degree Days",
            config_entry=entry,
            update_interval=timedelta(seconds=600),
        )

        data = dict(self.config_entry.data)
        options = dict(self.config_entry.options)
        normalized_options = {
            CONF_WEATHER_STATION: options.get(
                CONF_WEATHER_STATION,
                data.pop(CONF_WEATHER_STATION, DEFAULT_WEATHER_STATION),
            ),
            CONF_INDOOR_TEMP: options.get(
                CONF_INDOOR_TEMP,
                data.pop(CONF_INDOOR_TEMP, DEFAULT_INDOOR_TEMP),
            ),
            CONF_HEATING_LIMIT: options.get(
                CONF_HEATING_LIMIT,
                data.pop(CONF_HEATING_LIMIT, DEFAULT_HEATING_LIMIT),
            ),
            CONF_STARTDAY: options.get(
                CONF_STARTDAY,
                data.pop(CONF_STARTDAY, DEFAULT_STARTDAY),
            ),
            CONF_STARTMONTH: options.get(
                CONF_STARTMONTH,
                data.pop(CONF_STARTMONTH, DEFAULT_STARTMONTH),
            ),
            CONF_CONSUMPTION_SENSOR: options.get(
                CONF_CONSUMPTION_SENSOR,
                data.pop(CONF_CONSUMPTION_SENSOR, DEFAULT_CONSUMPTION_SENSOR),
            ),
            CONF_DHW_CONSUMPTION: options.get(
                CONF_DHW_CONSUMPTION,
                data.pop(CONF_DHW_CONSUMPTION, DEFAULT_DHW_CONSUMPTION),
            ),
            CONF_HEATPUMP: options.get(
                CONF_HEATPUMP,
                data.pop(CONF_HEATPUMP, DEFAULT_HEATPUMP),
            ),
        }

        if normalized_options != self.config_entry.options or data != self.config_entry.data:
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=data,
                options=normalized_options,
            )

        self.weather_station = normalized_options[CONF_WEATHER_STATION]
        self.indoor_temp = normalized_options[CONF_INDOOR_TEMP]
        self.heating_limit = normalized_options[CONF_HEATING_LIMIT]
        self.start_day = normalized_options[CONF_STARTDAY]
        self.start_month = normalized_options[CONF_STARTMONTH]
        self.total_consumption_sensor = normalized_options[CONF_CONSUMPTION_SENSOR]
        self.dhw_consumption = normalized_options[CONF_DHW_CONSUMPTION]
        self.heatpump = normalized_options[CONF_HEATPUMP]
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
        try:
            self.total_consumption_sensor_state = self.hass.states.get(self.total_consumption_sensor)
            self.total_consumption = float(self.total_consumption_sensor_state.state)
        except (AttributeError, TypeError, ValueError):
            self.total_consumption = 0
        try:
            data = await self.hass.async_add_executor_job(
                KNMI,
                self.startdate,
                self.weather_station,
                self.indoor_temp,
                self.heating_limit,
                self.total_consumption,
                self.dhw_consumption,
                self.heatpump
            )

        except (OSError, Timeout, HTTPError) as err:
            raise update_coordinator.UpdateFailed(err)

        self.logger.debug(
            "Connection to KNMI successful. Total sum degree days this year %s",
            data,
        )

        return data

    async def async_handle_consumption_sensor_change(self, event) -> None:
        """Refresh derived sensors when the source consumption sensor updates."""
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")

        if new_state is None or old_state == new_state:
            return

        await self.async_request_refresh()
