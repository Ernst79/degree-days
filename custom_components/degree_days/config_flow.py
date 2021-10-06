"""Config flow for degree days integration."""
import datetime
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_HEATING_LIMIT,
    CONF_INDOOR_TEMP,
    CONF_WEATHER_STATION,
    CONF_STARTDAY,
    CONF_STARTMONTH,
    CONF_GAS_CONSUMPTION,
    CONF_GAS_SENSOR,
    DEFAULT_HEATING_LIMIT,
    DEFAULT_INDOOR_TEMP,
    DEFAULT_NAME,
    DEFAULT_WEATHER_STATION,
    DEFAULT_STARTDAY,
    DEFAULT_STARTMONTH,
    DEFAULT_GAS_CONSUMPTION,
    DEFAULT_GAS_SENSOR,
    DOMAIN,
    MONTHS,
    STATION_MAPPING
)

_LOGGER = logging.getLogger(__name__)


@callback
def degree_days_entries(hass: HomeAssistant):
    """Return the weather station already configured."""
    return {
        entry.data[CONF_WEATHER_STATION] for entry in hass.config_entries.async_entries(DOMAIN)
    }


class DegreeDaysConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for degree days integration."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._errors: dict = {}

    async def async_step_user(self, user_input=None):
        """Step when user initializes a integration."""
        self._errors = {}

        if user_input is not None:
            valid_date = await self._date_validation(
                user_input[CONF_STARTDAY], user_input[CONF_STARTMONTH]
            )
            valid_station = await self._weather_station_in_configuration_exists(
                self.hass, user_input[CONF_WEATHER_STATION]
            )
            if not valid_date:
                 self._errors[CONF_STARTDAY] = "invalid_startday"
            elif not valid_station:
                self._errors[CONF_WEATHER_STATION] = "already_configured"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

        user_input = {}
        # Provide defaults for form
        user_input[CONF_NAME] = DEFAULT_NAME
        user_input[CONF_HEATING_LIMIT] = DEFAULT_HEATING_LIMIT
        user_input[CONF_INDOOR_TEMP] = DEFAULT_INDOOR_TEMP
        user_input[CONF_WEATHER_STATION] = DEFAULT_WEATHER_STATION
        user_input[CONF_STARTDAY] = DEFAULT_STARTDAY
        user_input[CONF_STARTMONTH] = DEFAULT_STARTMONTH
        user_input[CONF_GAS_CONSUMPTION] = DEFAULT_GAS_CONSUMPTION
        user_input[CONF_GAS_SENSOR] = DEFAULT_GAS_SENSOR

        return await self._show_config_form(user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return DegreeDaysOptionsFlowHandler(config_entry)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit config data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME, default=user_input.get(CONF_NAME, DEFAULT_NAME)
                    ): str,
                    vol.Optional(
                        CONF_HEATING_LIMIT, default=user_input.get(CONF_HEATING_LIMIT, DEFAULT_HEATING_LIMIT)
                    ): cv.positive_int,
                    vol.Optional(
                        CONF_INDOOR_TEMP, default=user_input.get(CONF_INDOOR_TEMP, DEFAULT_INDOOR_TEMP)
                    ): cv.positive_int,
                    vol.Required(
                        CONF_WEATHER_STATION, default=user_input.get(CONF_WEATHER_STATION, DEFAULT_WEATHER_STATION)
                    ): vol.In(list(STATION_MAPPING)),
                    vol.Required(
                        CONF_STARTDAY, default=user_input.get(CONF_STARTDAY, DEFAULT_STARTDAY)
                    ): cv.positive_int,
                    vol.Required(
                        CONF_STARTMONTH, default=user_input.get(CONF_STARTMONTH, DEFAULT_STARTMONTH)
                    ):  vol.In(MONTHS),
                    vol.Optional(
                        CONF_GAS_CONSUMPTION, default=user_input.get(CONF_GAS_CONSUMPTION, DEFAULT_GAS_CONSUMPTION)
                    ): cv.positive_int,
                    vol.Optional(
                        CONF_GAS_SENSOR, default=user_input.get(CONF_GAS_SENSOR, DEFAULT_GAS_SENSOR)
                    ): str,
                }
            ),
            errors=self._errors,
        )
    async def _date_validation(self, startday, startmonth) -> bool:
        """Return True if day and month is a correct date."""
        isValidDate = True
        try:
            datetime.datetime.strptime(
                "2021" + startmonth + str(startday), "%Y%B%d"
            )
            return True
        except ValueError:
            return False

    async def weather_station_in_configuration_exists(hass, weather_station_entry) -> bool:
        """Return True if weather station exists in configuration."""
        if weather_station_entry in degree_days_entries(hass):
            return True
        return False

class DegreeDaysOptionsFlowHandler(config_entries.OptionsFlow):
    """Blueprint config flow options handler."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self._errors: dict = {}
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.options.update(user_input)
            valid_date = await self._date_validation(
                user_input[CONF_STARTDAY], user_input[CONF_STARTMONTH]
            )
            if not valid_date:
                 self._errors[CONF_STARTDAY] = "invalid_startday"
            else:
                return await self._update_options()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME, default=self.options.get(CONF_NAME, DEFAULT_NAME)
                    ): str,
                    vol.Optional(
                        CONF_HEATING_LIMIT, default=self.options.get(CONF_HEATING_LIMIT, DEFAULT_HEATING_LIMIT)
                    ): cv.positive_int,
                    vol.Optional(
                        CONF_INDOOR_TEMP, default=self.options.get(CONF_INDOOR_TEMP, DEFAULT_INDOOR_TEMP)
                    ): cv.positive_int,
                    vol.Required(
                        CONF_WEATHER_STATION, default=self.options.get(CONF_WEATHER_STATION, DEFAULT_WEATHER_STATION)
                    ): vol.In(list(STATION_MAPPING)),
                    vol.Required(
                        CONF_STARTDAY, default=self.options.get(CONF_STARTDAY, DEFAULT_STARTDAY)
                    ): cv.positive_int,
                    vol.Required(
                        CONF_STARTMONTH, default=self.options.get(CONF_STARTMONTH, DEFAULT_STARTMONTH)
                    ):  vol.In(MONTHS),
                    vol.Optional(
                        CONF_GAS_CONSUMPTION, default=self.options.get(CONF_GAS_CONSUMPTION, DEFAULT_GAS_CONSUMPTION)
                    ): cv.positive_int,
                    vol.Optional(CONF_GAS_SENSOR, default=self.options.get(CONF_GAS_SENSOR, DEFAULT_GAS_SENSOR)
                    ): str,
                }
            ),
            errors=self._errors,
        )

    async def _update_options(self):
        """Update config entry options."""
        return self.async_create_entry(
            title=self.config_entry.data.get(CONF_NAME), data=self.options
        )

    async def _date_validation(self, startday, startmonth) -> bool:
        """Return True if day and month is a correct date."""
        isValidDate = True
        try:
            datetime.datetime.strptime(
                "2021" + startmonth + str(startday), "%Y%B%d"
            )
            return True
        except ValueError:
            return False
