"""The Länderübergreifendes Hochwasser Portal API - Functions for Niedersachsen."""

from __future__ import annotations

from .api_utils import (
    DynamicData,
    LHPError,
    StaticData,
    convert_to_datetime,
    convert_to_float,
    convert_to_int,
    fetch_json,
)


def init_NI(ident: str) -> StaticData:  # pylint: disable=invalid-name
    """Init data for Niedersachsen."""
    try:
        # Get data
        data = fetch_json(
            "https://bis.azure-api.net/PegelonlinePublic/REST/stammdaten"
            + "/stationen/All?key=9dc05f4e3b4a43a9988d747825b39f43"
        )
        # Parse data
        for entry in data["getStammdatenResult"]:
            if entry["STA_Nummer"] == ident[3:]:
                name = entry["Name"] + " / " + entry["GewaesserName"]
                internal_url = (
                    "https://bis.azure-api.net/PegelonlinePublic/REST/stammdaten/stationen/"
                    + str(entry["STA_ID"])
                    + "?key=9dc05f4e3b4a43a9988d747825b39f43"
                )
                url = (
                    "https://www.pegelonline.nlwkn.niedersachsen.de/Pegel/Karte/Binnenpegel/ID/"
                    + str(entry["STA_ID"])
                )
                if entry["Internetbeschreibung"] != "Keine Daten":
                    hint = entry["Internetbeschreibung"]
                else:
                    hint = None
                return StaticData(
                    ident=ident,
                    name=name,
                    internal_url=internal_url,
                    url=url,
                    hint=hint,
                )
        return StaticData(ident=ident)
    except Exception as err:
        raise LHPError(err, "ni_api.py: init_NI()") from err


def update_NI(static_data: StaticData) -> DynamicData:  # pylint: disable=invalid-name
    """Update data for Niedersachsen."""
    try:
        # Get data
        data = fetch_json(static_data.internal_url)
        # Parse data
        try:
            stage = convert_to_int(
                data["getStammdatenResult"][0]["Parameter"][0]["Datenspuren"][0][
                    "AktuelleMeldeStufe"
                ]
            )
        except (IndexError, KeyError):
            stage = None
        try:
            value = convert_to_float(
                data["getStammdatenResult"][0]["Parameter"][0]["Datenspuren"][0][
                    "AktuellerMesswert"
                ]
            )
        except (IndexError, KeyError):
            value = None
        try:
            if data["getStammdatenResult"][0]["Parameter"][0]["Einheit"] == "cm":
                level = value
                flow = None
            elif data["getStammdatenResult"][0]["Parameter"][0]["Einheit"] == "m³/s":
                level = None
                flow = value
            else:
                level = None
                flow = None
        except (IndexError, KeyError):
            level = None
            flow = None
        try:
            last_update = convert_to_datetime(
                data["getStammdatenResult"][0]["Parameter"][0]["Datenspuren"][0][
                    "AktuellerMesswert_Zeitpunkt"
                ],
                "%d.%m.%Y %H:%M",
            )
        except (IndexError, KeyError):
            last_update = None
        return DynamicData(level=level, stage=stage, flow=flow, last_update=last_update)
    except Exception as err:
        raise LHPError(err, "ni_api.py: update_NI()") from err
