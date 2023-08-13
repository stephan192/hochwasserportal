# hochwasserportal

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
[![Validate with hassfest](https://github.com/stephan192/hochwasserportal/actions/workflows/hassfest.yml/badge.svg)](https://github.com/stephan192/hochwasserportal/actions/workflows/hassfest.yml)
[![HACS Action](https://github.com/stephan192/hochwasserportal/actions/workflows/hacs.yml/badge.svg)](https://github.com/stephan192/hochwasserportal/actions/workflows/hacs.yml)

This Home Assistant integration started as integration for the [Länderübergreifendes Hochwasser Portal (LHP)](https://www.hochwasserzentralen.de), but due to the fact that the LHP locked their formerly open API in July 2023 this integration was rewritten the query the 16 state portals to get all information. The positive side effect, now more pegel are available, because the different state portals didn't report all their pegel to the LHP. The negativ side effect, some of the state portals need to be queried by web scraping and therefore need to be adjusted if the portal's design changes.

## List of supported values
* :heavy_check_mark: Value mostly available. Check individual state portal because not all pegel report all values.
* :x: Value generally yet not available.

| Ident | State                  | Level              | Stage              | Flow               | Portal |
|-------|------------------------|--------------------|--------------------|--------------------|--------|
| BB    | Brandenburg            | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | [Pegelportal Brandenburg](https://pegelportal.brandenburg.de) |
| BE    | Berlin                 | :x:                | :x:                | :x:                | [Wasserportal Berlin](https://wasserportal.berlin.de) |
| BW    | Baden-Württemberg      | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | [Hochwasservorhersagezentrale Baden-Württemberg](https://www.hvz.baden-wuerttemberg.de) |
| BY    | Bayern                 | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | [Hochwassernachrichtendienst Bayern](https://www.hnd.bayern.de) |
| HB    | Bremen                 | :x:                | :x:                | :x:                | [Pegelstände Bremen](https://geoportale.dp.dsecurecloud.de/pegelbremen) |
| HE    | Hessen                 | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | [Hochwasserportal Hessen](https://www.hochwasser-hessen.de) |
| HH    | Hamburg                | :x:                | :x:                | :x:                | [HPA HydroOnline](https://hydroonline.hpanet.de) |
| MV    | Mecklenburg-Vorpommern | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | [Pegelportal Mecklenburg-Vorpommern](https://pegelportal-mv.de) |
| NI    | Niedersachsen          | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | [NLWKN Pegelonline](https://www.pegelonline.nlwkn.niedersachsen.de) |
| NW    | Nordrhein-Westfalen    | :heavy_check_mark: | :heavy_check_mark: | :x:                | [Hochwassermeldedienst NRW](https://www.hochwasserportal.nrw.de)|
| RP    | Rheinland-Pfalz        | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | [Hochwasservorhersagedienst - Landesamt für Umwelt Rheinland-Pfalz](https://hochwasser.rlp.de)|
| SH    | Schleswig-Holstein     | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | [Hochwasser-Sturmflut-Information Schleswig-Holstein](https://hsi-sh.de) |
| SL    | Saarland               | :heavy_check_mark: | :heavy_check_mark: | :x:                | [Pegel Saarland](https://www.saarland.de/mukmav/DE/portale/wasser/informationen/hochwassermeldedienst/wasserstaende_warnlage/wasserstaende_warnlage_node.html) |
| SN    | Sachsen                | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | [Landeshochwasserzentrum Sachsen](https://www.umwelt.sachsen.de/umwelt/infosysteme/hwims/portal/web/wasserstand-uebersicht) |
| ST    | Sachsen-Anhalt         | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | [Landesportal Sachsen-Anhalt](https://hochwasservorhersage.sachsen-anhalt.de) |
| TH    | Thüringen              | :heavy_check_mark: | :x:                | :heavy_check_mark: | [Hochwassernachrichtenzentrale Thüringen](https://hnz.thueringen.de/hw-portal) |

## Notes
* Not all stream gauges report all three values. If one or more values are unavailable check official site if stream gauge is down or if not which values are reported.
* `Level` reports the actual water level (in German *Pegelstand* or colloquially *Wasserstand*). A value in centimetres, starting from 0 cm = *Pegelnullpunktshöhe*.
* `Stage` reports the actual warning stage (in German depending on ferderal state e.g. *Meldestufe* in Bavaria, *Alarmstufe* in Brandenburg). A number between 0 (=no flood) and 4 (= very large flood).
* `Flow` reports the actual flow rate (in German *Abfluss* or *Durchfluss*). A value in m³/s.

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
* Add the integration by pressing the **"+ADD INTEGRATION"** on the **Settings - Integrations** page and select **"Länderübergreifendes Hochwasser Portal"** from the drop-down menu.
* Enter a valid pegel-ID. **A full list of valid pegels can be found [here](https://github.com/stephan192/hochwasserportal/blob/main/pegel.md).**
* For multiple locations, just repeat with each pegel-ID.

## Result
![Example 1](https://github.com/stephan192/hochwasserportal/blob/main/example.png)
