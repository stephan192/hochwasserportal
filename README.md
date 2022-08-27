# hochwasserportal

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
For multiple locations, just repeat with each pegel-ID.  
The variables `level`, `stage` and `flow` are optional and default to `True` if not set. If you don't want one of the three sensors to show up you have to set the corresponding variable to `False`.  
**A full list of valid pegels can be found [here](https://github.com/stephan192/hochwasserportal/blob/main/pegel.md).**

After **restarting** your Home Assistant installation the following three sensors should show up.  
![Example 1](https://github.com/stephan192/hochwasserportal/blob/main/example.png)
