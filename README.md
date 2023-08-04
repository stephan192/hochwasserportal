# hochwasserportal

# This integration is currently only working for BY, NI, NW, SH, SN, ST and TH pegel because the formerly used API has been locked from public usage! I'll try to repair the other pegel also.

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
[![Validate with hassfest](https://github.com/stephan192/hochwasserportal/actions/workflows/hassfest.yml/badge.svg)](https://github.com/stephan192/hochwasserportal/actions/workflows/hassfest.yml)
[![HACS Action](https://github.com/stephan192/hochwasserportal/actions/workflows/hacs.yml/badge.svg)](https://github.com/stephan192/hochwasserportal/actions/workflows/hacs.yml)

Home Assistant integration for [Länderübergreifendes Hochwasser Portal](https://www.hochwasserzentralen.de)

Sources
* https://bundesapi.github.io/hochwasserzentralen-api
* https://github.com/bundesAPI/hochwasserzentralen-api

# Setup

## Installation via HACS
* Ensure that HACS is installed
* Search for and install the "hochwasserportal" integration
* **Restart Home Assistant**

## Manual installation
* Copy the sources from `ROOT_OF_THIS_REPO/custom_components/hochwasserportal` to `YOUR_HA_INSTALLATION/config/custom_components/hochwasserportal`
* **Restart Home Assistant**

## Configuration
* The integration can only be configured by using config flow.
* Add the integration by pressing the "+ADD INTEGRATION" on the Settings - Integrations page and select "Länderübergreifendes Hochwasser Portal" from the drop-down menu.
* Enter a valid pegel-ID. **A full list of valid pegels can be found [here](https://github.com/stephan192/hochwasserportal/blob/main/pegel.md).**
* For multiple locations, just repeat with each pegel-ID.

## Result
![Example 1](https://github.com/stephan192/hochwasserportal/blob/main/example.png)

**Notes:**  
* Not all stream gauges report all three values. If one or more values are unavailable check [official site](https://www.hochwasserzentralen.de) if stream gauge is down or if not which values are reported.
* `level` reports, except for the Dutch stream gauges, the actual water level (in German *Pegelstand* or colloquially *Wasserstand*). A value in centimetres, starting from 0 cm = *Pegelnullpunktshöhe*. The Dutch stream gauges report a value in centimetres starting from 0 cm = [*Normaal Amsterdams Peil*](https://de.wikipedia.org/wiki/Amsterdamer_Pegel). *W value* on [official site](https://www.hochwasserzentralen.de).
* `stage` reports the actual warning stage (in German depending on ferderal state e.g. *Meldestufe* in Bavaria, *Alarmstufe* in Brandenburg). A number between 0 (=no flood) and 4 (= very large flood). *Text message* on [official site](https://www.hochwasserzentralen.de).
* `flow` reports the actual flow rate (in German *Abfluss* or *Durchfluss*). A value in m³/s. *Q value* on [official site](https://www.hochwasserzentralen.de).
