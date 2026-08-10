# Changelog

## 1.3.3

- Restore `measurement` state class for forecast and ratio sensors so Home Assistant long-term statistics and repair warnings behave correctly.
- Prevent a division-by-zero warning when the contract year starts in summer and weighted degree days are still zero.
- Keep prognosis sensors available during that zero-WDD period by using a domestic-hot-water-only fallback until the first heating degree day is recorded.
- Add a one-time runtime info log when that temporary zero-WDD fallback is active.

## 1.3.3-beta.7

- Restore `measurement` state class for forecast and ratio sensors so Home Assistant long-term statistics and repair warnings behave correctly.

## 1.3.3-beta.6

- Prevent a division-by-zero warning when the contract year starts in summer and weighted degree days are still zero.
- Keep prognosis sensors available during that zero-WDD period by using a domestic-hot-water-only fallback until the first heating degree day is recorded.
- Add a one-time runtime info log when that temporary zero-WDD fallback is active.

## 1.3.3-beta.5

- Fall back to De Bilt reference averages when the selected KNMI station has insufficient historical data for the prognosis reference period.
- Log the prognosis reference fallback only once per runtime.
- Remove the manual refresh button again.
