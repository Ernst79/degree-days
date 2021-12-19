"""Constants for the Degree Days integration."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
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
CONF_STARTDAY = "startday"
CONF_STARTMONTH = "startmonth"
CONF_GAS_SENSOR = "gas sensor"
CONF_GAS_USE_OTHER = "gas use other"

DEFAULT_HEATING_LIMIT = 18.0
DEFAULT_INDOOR_TEMP = 18.0
DEFAULT_WEATHER_STATION = "De Bilt"
DEFAULT_STARTDAY = "01"
DEFAULT_STARTMONTH = "January"
DEFAULT_GAS_SENSOR = ""
DEFAULT_GAS_USE_OTHER = 0

# KNMI weather stations (NL).
STATION_MAPPING = {
    'Arcen': 391,
    'Berkhout': 249,
    'Cabauw Mast': 348,
    'Cadzand ': 308,
    'De Bilt': 260,
    'De Kooy': 235,
    'Deelen': 275,
    'Eelde': 280,
    'Eindhoven': 370,
    'Ell': 377,
    'Gilze-Rijen': 350,
    'Herwijnen': 356,
    'Hansweert': 315,
    'Heino': 278,
    'Hoek van Holland': 330,
    'Hoofdplaat': 311,
    'Hoogeveen': 279,
    'Hoorn Terschelling': 251,
    'Houtribdijk': 258,
    'Hupsel': 283,
    'Huibertgat': 285,
    'IJmond': 209,
    'IJmuiden': 225,
    'Lauwersoog': 277,
    'Leeuwarden': 270,
    'Lelystad': 269,
    'Maastricht': 380, 
    'Marknesse': 273,
    'Nieuw Beerta': 286,
    'Oosterschelde': 312,
    'Rotterdam': 344,
    'Rotterdam Geulhaven': 343,
    'Schaar': 316,
    'Schiphol': 240,
    'Soesterberg': 265,
    'Stavenisse': 324,
    'Stavoren': 267,
    'Tholen': 331,
    'Twenthe': 290,
    'Valkenburg Zh': 210,
    'Vlakte van De Raan': 313,
    'Vlieland': 242,
    'Vlissingen': 310,
    'Volkel': 375,
    'Voorschoten': 215,
    'Westdorpe': 319,
    'Wijdenes': 248,
    'Wijk aan Zee': 257,
    'Wilhelminadorp': 323,
    'Woensdrecht': 340,
}
# Weigh factor per month for weighted degree days
WEIGHT_FACTOR = {
    1: 1.1,
    2: 1.1,
    3: 1.0,
    4: 0.8,
    5: 0.8,
    6: 0.8,
    7: 0.8,
    8: 0.8,
    9: 0.8,
    10: 1.0,
    11: 1.1,
    12: 1.1
}
MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December"
]

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
        state_class=SensorStateClass.TOTAL,
    ),
    DegreeDaysSensorEntityDescription(
        key="weighted_degree_days_year",
        name="weighted degree days this year",
        icon="mdi:thermometer",
        native_unit_of_measurement=TEMP_CELSIUS,
        device_class=None,
        state_class=SensorStateClass.TOTAL,
    ),
    DegreeDaysSensorEntityDescription(
        key="gas_per_weighted_degree_day",
        name="gas consumption per weighted degree day",
        icon="mdi:fire",
        native_unit_of_measurement=VOLUME_CUBIC_METERS,
        device_class=SensorDeviceClass.GAS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    DegreeDaysSensorEntityDescription(
        key="gas_prognose",
        name="gas prognose",
        icon="mdi:fire",
        native_unit_of_measurement=VOLUME_CUBIC_METERS,
        device_class=SensorDeviceClass.GAS,
        state_class=SensorStateClass.TOTAL,
    ),
)
