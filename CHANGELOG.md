# Changelog

## 1.3.4-beta.1

- Keep `measurement` for forecast and ratio sensors, but remove the gas/energy device class so Home Assistant accepts the entity metadata again.
- Preserve the zero-WDD prognosis fallback from the previous beta series.

## 1.3.3

- Restore `measurement` state class for forecast and ratio sensors so Home Assistant long-term statistics and repair warnings behave correctly.
- Prevent a division-by-zero warning when the contract year starts in summer and weighted degree days are still zero.
- Keep prognosis sensors available during that zero-WDD period by using a domestic-hot-water-only fallback until the first heating degree day is recorded.
- Add a one-time runtime info log when that temporary zero-WDD fallback is active.
