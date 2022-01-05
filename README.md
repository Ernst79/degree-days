# Degree-days integration

Degree days integration for Home Assistant based on KNMI weather station data (the Netherlands) and your current gas consumpition this year. 

This integration will collect daily averaged temperatures of the last year from a KNMI weather station and will calculate the total number of (weighted) degree days this year (similar as is done on the [mindergas website](www.mindergas.nl)). Based on this information and input from your gas consumption so far this year, it will estimate the gas consumption for the entire year and will determine the gas consumption per weighted degree day, which can be used for comparison with other years or other houses.

## (Weighted) degree days
For more information on degree days and its use, have a look at the website [Degree Days.net](https://www.degreedays.net/) (English) or [Mindergas](https://mindergas.nl/degree_days/explanation) (Dutch). 

In the current implementation, we follow the approach of Mindergas. Weigthed degree days are determined by multiplying the number of degree days in a certain month with a certain factor. The applied multiplication factors are:

- April till September: 0,8
- March and October: 1,0
- November till Februari: 1,1

## Gas prognose and comparison

You can add a gas sensor to calculate the gas consumption per weighted degree day from the start of the year, which can be used to compare your gas consumption with other users or previous years. Comparison based on gas consumption per weighted degree day corrects for effects of a cold or warm, which gives you a better insight into the effect of e.g. insulation or the expansion of your family, on your gas consumption. The integration will also calculate a prognose for the gas consumption for the current year.

## How to install

1. Install Degree-days via [hacs](https://hacs.xyz/)
2. Reboot HA
3. In HA goto Config -> integrations. Add Degree-days integration.
4. In your lovelace dashboard, add a card with the degree days entities.

## Options

The Degree Days integration has the following options:

**Weather station (KNMI)**

KNMI Weather station to get the daily mean outdoor temperatures. Currently only Dutch weather stations are supported. 

**Mean indoor temperature**

Estimated daily mean indoor temperature during day and night, averaged over one year. Default setting: 18°C.

**Heating temperature limit**

In the spring and autumn, the heating will not always be turned on directly, even if the daily mean outdoor temperature is below the daily mean indoor temperature. Buildings will collect heat during hot periods in e.g. concrete walls, which is released gradually, preventing the heating to turn on. By setting a different heating temperature limit (e.g. 15,5°C), degree days will only be counted if the daily mean outdoor temperature is lower than this heating temperature limit. A lower value for the heating temperature will increase the gas consumption per degree day in the spring and autumn. 

**Startday for sum of total degree days**

Day of the month from which the yearly totals are computed. When used in combination with a gas sensor, this has to be the same day as the yearly total gas consumption is determined. 

**Startmonth for sum of total degree days**

Month from which the yearly totals are computed. When used in combination with a gas sensor, this has to be the same day as the yearly total gas consumption is determined. 

**Gas sensor entity**

Gas sensor entity with the total consumption this year.

**Monthly gas usage for shower, bath and cooking**

Monthly gas usage for shower, bath and cooking. This will be substracted from your gas consumption, before calculating the gas usage per weighted degree day.
