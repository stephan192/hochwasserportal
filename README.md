# hochwasserportal

# This integration is not working anymore because the underlying API has been locked from public usage! Maybe i find a solution in future but currently you can uninstall it!

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

## Configuration (Example for the Isar in Munich)
Add the following lines to your `configuration.yaml`
```
sensor:
  - platform: hochwasserportal
    pegel: BY_16005701
    level: True
    stage: True
    flow: True
```

**Notes:**  
* **A full list of valid pegels can be found [here](https://github.com/stephan192/hochwasserportal/blob/main/pegel.md).**
* For multiple locations, just repeat with each pegel-ID.
* The parameters `level`, `stage` and `flow` are optional and default to `True` if not set. If you don't want one of the three sensors to show up you have to set the corresponding variable to `False`.

## Result
After **restarting** your Home Assistant installation the following three sensors should show up.  
![Example 1](https://github.com/stephan192/hochwasserportal/blob/main/example.png)

**Notes:**  
* Not all stream gauges report all three values. If one or more values are unavailable check [official site](https://www.hochwasserzentralen.de) if stream gauge is down or if not which values are reported.
* `level` reports, except for the Dutch stream gauges, the actual water level (in German *Pegelstand* or colloquially *Wasserstand*). A value in centimetres, starting from 0 cm = *Pegelnullpunktshöhe*. The Dutch stream gauges report a value in centimetres starting from 0 cm = [*Normaal Amsterdams Peil*](https://de.wikipedia.org/wiki/Amsterdamer_Pegel). *W value* on [official site](https://www.hochwasserzentralen.de).
* `stage` reports the actual warning stage (in German depending on ferderal state e.g. *Meldestufe* in Bavaria, *Alarmstufe* in Brandenburg). A number between 0 (=no flood) and 4 (= very large flood). *Text message* on [official site](https://www.hochwasserzentralen.de).
* `flow` reports the actual flow rate (in German *Abfluss* or *Durchfluss*). A value in m³/s. *Q value* on [official site](https://www.hochwasserzentralen.de).
