# Degree-days integration

Degree days integration for Home Assistant based on KNMI weather station data (the Netherlands)

This integration will collect daily average temperature from a KNMI weather station and will calculate the total number of degree days and the weighted total number of degree days this year (similar as is done on the [mindergas website](www.mindergas.nl)).

Weigthed degree days are determined by multiplying the number of degree days in a certain month with a certain factor. The applied multiplication factors are:

- April till September: 0,8
- March and October: 1,0
- November till Februari: 1,1

You can add a gas sensor to calculate the gas consumption per weighted degree day from the start of the year, which can be used to compare your gas usage with other users or previous years, taking into account the temperature in a certain year. For more information on degree days and its use, have a look at the website [Degree Days.net](https://www.degreedays.net/) (English) or [Mindergas](https://mindergas.nl/degree_days/explanation) (Dutch)

The Degree Days integration has the following options


- **Weather station (KNMI)**
KNMI Weather station to get the daily mean outdoor temperatures. Currently only Dutch weather stations are supported. 

- **Mean indoor temperature**
Estimated daily mean indoor temperature during day and night, averaged over one year. Default setting: 18°C.

- **Heating temperature limit**
In the spring and autumn, the heating will not always be turned on directly, even if the daily mean outdoor temperature is below the daily mean indoor temperature. Buildings will collect heat during hot periods in e.g. concrete walls, which is released gradually, preventing the heating to turn on. By setting a different heating temperature limit (e.g. 15,5°C), degree days will only be counted if the daily mean outdoor temperature is lower than this heating temperature limit. A lower value for the heating temperature will increase the gas consumption per degree day in the spring and autumn. 

- **Startday for sum of total degree days**
Day of the month from which the yearly totals are computed. When used in combination with a gas sensor, this has to be the same day as the yearly total gas consumption is determined. 

- **Startmonth for sum of total degree days**
Month from which the yearly totals are computed. When used in combination with a gas sensor, this has to be the same day as the yearly total gas consumption is determined. 

- **Gas sensor entity**
Gas sensor entity with the total consumption this year.