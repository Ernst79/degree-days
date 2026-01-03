# Degree-days integration

Degree days integration for Home Assistant based on KNMI weather station data (the Netherlands) and your current gas consumption this year.

This integration will collect daily averaged temperatures of the last year from a KNMI weather station and will calculate the total number of (weighted) degree days this year (similar as is done on the [mindergas website](https://www.mindergas.nl)). Based on this information and input from your gas/heatpump consumption so far this year, it will estimate the gas/energy consumption for the entire year and will determine the gas/energy consumption per weighted degree day, which can be used for comparison with other years or other houses.

## (Weighted) degree days
For more information on degree days and its use, have a look at the website [Degree Days.net](https://www.degreedays.net/) (English) or [Mindergas](https://mindergas.nl/degree_days/explanation) (Dutch).

In the current implementation, we follow the approach of Mindergas. Weighted degree days are determined by multiplying the number of degree days in a certain month with a certain factor. The applied multiplication factors are:

- April till September: 0,8
- March and October: 1,0
- November till Februari: 1,1

## Gas/energy prognose and comparison

You can add a gas or energy sensor to calculate the consumption per weighted degree day from the start of the year, which can be used to compare your consumption with other users or previous years. Comparison based on consumption per weighted degree day corrects for effects of a cold or warm, which gives you a better insight into the effect of e.g. insulation or change in the number of family members, on your gas/energy consumption. The integration will also calculate a prognose for the gas/energy consumption for the current year.

## How to install

1. Make sure you have [hacs](https://hacs.xyz/) installed.
2. In hacs, first add a custom repository, with type: integration and add the following link in the integration field: https://github.com/Ernst79/degree-days
3. In hacs, go to integrations and click on the blue button `Exlore and download repositories` in the bottom left corner, search for `Degree-days` and install it.
4. Reboot HA.
5. In HA go to Config -> Integrations. Add the Degree-days integration to HA.
6. select your weather station and add your gas/heatpump sensor and check the other settings.
7. click submit.
8. In your lovelace dashboard, add a card with the degree days entities.

## Options

The Degree Days integration has the following options:

**Weather station (KNMI)**

KNMI Weather station to get the daily mean outdoor temperatures. Currently only Dutch weather stations are supported.

**Mean indoor temperature**

Estimated daily mean indoor temperature during day and night, averaged over one year. Default setting: 18°C.

**Heating temperature limit**

In the spring and autumn, the heating will not always be turned on directly, even if the daily mean outdoor temperature is below the daily mean indoor temperature. Buildings will collect heat during hot periods in e.g. concrete walls, which is released gradually, preventing the heating to turn on. By setting a different heating temperature limit (e.g. 15,5°C), degree days will only be counted if the daily mean outdoor temperature is lower than this heating temperature limit. A lower value for the heating temperature will increase the gas/energy consumption per degree day in the spring and autumn.

**Startday for sum of total degree days**

Day of the month from which the yearly totals are computed. When used in combination with a gas/energy sensor, this has to be the same day as the total consumption is determined from. E.g. if your gas sensor reports the total gas consumption starting at the 14th of February, set the Startday for the sum of total degree days to the 14th.

**Startmonth for sum of total degree days**

Month from which the yearly totals are computed. When used in combination with a gas/energy sensor, this has to be the same month as the total consumption is determined from. E.g. if your gas sensor reports the total gas consumption starting at the 14th of February, set the Startmonth for the sum of total degree days to the February.

**Gas/Energy sensor entity**

Gas/Energy sensor entity with the total consumption of gas in m3 or Energy in kWh, starting at the set Startday and Startmonth of the current year. You may have to use a utility_meter helper in Home Assistant to determine that data.

**Monthly gas/energy usage for shower, bath and cooking**

Monthly gasenergy usage for shower, bath and cooking. This will be subtracted from your gas consumption, before calculating the gas/energy usage per weighted degree day.

**Heatpump/Electric heating**

Enable this option if you want to use kWh instead of m3, e.g. when you use a heatpump.
