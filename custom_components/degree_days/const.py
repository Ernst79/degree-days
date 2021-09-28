"""Constants for the Degree Days integration."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    STATE_CLASS_MEASUREMENT,
    STATE_CLASS_TOTAL_INCREASING,
    SensorEntityDescription,
)
from homeassistant.const import (
    VOLUME_CUBIC_METERS,
    TEMP_CELSIUS,
)
from homeassistant.util import dt

DOMAIN = "degree_days"

# Default config for degree days integration.
CONF_HEATING_LIMIT = "heating limit"
CONF_INDOOR_TEMP = "mean indoor temperature"
CONF_WEATHER_STATION = "weather station"
DEFAULT_HEATING_LIMIT = 15.5
DEFAULT_INDOOR_TEMP = 18.0
DEFAULT_NAME = "degree days"
DEFAULT_WEATHER_STATION = 240


@dataclass
class DegreeDaysSensorEntityDescription(SensorEntityDescription):
    """Describes Degree Days sensor entity."""


SENSOR_TYPES: tuple[DegreeDaysSensorEntityDescription, ...] = (
    DegreeDaysSensorEntityDescription(
        key="total_degree_days_this_year",
        name="degree days this year",
        icon="mdi:thermometer",
        native_unit_of_measurement=TEMP_CELSIUS,
        device_class=None,
        state_class=STATE_CLASS_TOTAL_INCREASING,
    ),
    DegreeDaysSensorEntityDescription(
        key="weighted_degree_days_year",
        name="weighted degree days this year",
        icon="mdi:thermometer",
        native_unit_of_measurement=TEMP_CELSIUS,
        device_class=None,
        state_class=STATE_CLASS_TOTAL_INCREASING,
    ),
)
