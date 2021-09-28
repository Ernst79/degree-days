"""Config flow for degree days integration."""
import logging
from urllib.parse import ParseResult, urlparse

from requests.exceptions import HTTPError, Timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.util import slugify

from .const import (
    CONF_HEATING_LIMIT,
    CONF_INDOOR_TEMP,
    CONF_WEATHER_STATION,
    DEFAULT_HEATING_LIMIT,
    DEFAULT_INDOOR_TEMP,
    DEFAULT_NAME,
    DEFAULT_WEATHER_STATION,
    DOMAIN
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

    def _weather_station_in_configuration_exists(self, weather_station_entry) -> bool:
        """Return True if weather station exists in configuration."""
        if weather_station_entry in degree_days_entries(self.hass):
            return True
        return False

    async def async_step_user(self, user_input=None):
        """Step when user initializes a integration."""
        self._errors = {}
        if user_input is not None:
            # set some defaults in case we need to return to the form
            name = slugify(user_input.get(CONF_NAME, DEFAULT_NAME))
            heating_limit = user_input.get(CONF_HEATING_LIMIT, DEFAULT_HEATING_LIMIT)
            indoor_temp = user_input.get(CONF_INDOOR_TEMP, DEFAULT_INDOOR_TEMP)
            weather_station_entry = user_input.get(CONF_WEATHER_STATION, DEFAULT_WEATHER_STATION)

            if self._weather_station_in_configuration_exists(weather_station_entry):
                self._errors[CONF_WEATHER_STATION] = "already_configured"
            else:
                return self.async_create_entry(title=name, data={
                    CONF_HEATING_LIMIT: heating_limit,
                    CONF_INDOOR_TEMP: indoor_temp,
                    CONF_WEATHER_STATION: weather_station_entry
                })
        else:
            user_input = {}
            user_input[CONF_NAME] = DEFAULT_NAME
            user_input[CONF_HEATING_LIMIT] = DEFAULT_HEATING_LIMIT
            user_input[CONF_INDOOR_TEMP] = DEFAULT_INDOOR_TEMP
            user_input[CONF_WEATHER_STATION] = DEFAULT_WEATHER_STATION

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
                    ): str,
                }
            ),
            errors=self._errors,
        )

    # async def async_step_import(self, user_input=None):
    #     """Import a config entry."""
    #     weather_station_entry = user_input.get(CONF_WEATHER_STATION, DEFAULT_WEATHER_STATION)
    #     weather_station_entry = user_input.get(CONF_WEATHER_STATION, DEFAULT_WEATHER_STATION)
    #     weather_station_entry = user_input.get(CONF_WEATHER_STATION, DEFAULT_WEATHER_STATION)

    #     if self._weather_station_in_configuration_exists(weather_station_entry):
    #         return self.async_abort(reason="already_configured")
    #     return await self.async_step_user(user_input)
