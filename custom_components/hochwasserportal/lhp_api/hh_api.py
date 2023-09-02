"""The Länderübergreifendes Hochwasser Portal API - Functions for Hamburg."""

from __future__ import annotations

from .api_utils import (
    DynamicData,
    LHPError,
    StaticData,
    convert_to_datetime,
    convert_to_float,
    convert_to_int,
    fetch_soup,
)


def init_HH(ident: str) -> StaticData:  # pylint: disable=invalid-name
    """Init data for Hamburg."""
    try:
        # Get data
        soup = fetch_soup("https://www.wabiha.de/karte.html")
        tooltipwrapper = soup.find("div", id="tooltipwrapper")
        div = tooltipwrapper.find_next("div", id="tooltip-content-" + ident[3:])
        spans = div.find_all("span")
        # Parse data
        if len(spans) == 8:
            text = div.getText()
            name = text[: text.find("Gewässer:")].strip()
            name = (
                name
                + " / "
                + text[
                    text.find("Gewässer:") + 9 : text.find("Niederschlagsvorhersage")
                ].strip()
            )
            url = "https://www.wabiha.de/grafik-" + ident[3:] + ".html"
            return StaticData(ident=ident, name=name, url=url)
        return StaticData(ident=ident)
    except Exception as err:
        raise LHPError(err, "hh_api.py: init_HH()") from err


def update_HH(static_data: StaticData) -> DynamicData:  # pylint: disable=invalid-name
    """Update data for Hamburg."""
    try:
        # Get data
        soup = fetch_soup("https://www.wabiha.de/karte.html")
        tooltipwrapper = soup.find("div", id="tooltipwrapper")
        div = tooltipwrapper.find_next(
            "div", id="tooltip-content-" + static_data.ident[3:]
        )
        spans = div.find_all("span")
        # Parse data
        if len(spans) == 8:
            text = div.getText()
            level = convert_to_float(
                text[
                    text.find("Wasserstand") + 11 : text.find("[NHN\u00A0+/-\u00A0cm]")
                ]
                .replace(".", "")
                .strip()
            )
            last_update = convert_to_datetime(
                text[
                    text.find("\u00A0\u00A0\u00A0 um") + 6 : text.find("Trend")
                ].strip(),
                "%d.%m.%Y %H:%M",
            )
            stage = convert_to_int(spans[7].attrs["class"][-1].split("_")[-1])
            if stage == 2:
                # Special case for Hamburg, see https://www.hochwasserzentralen.de/info
                stage = 3
            return DynamicData(level=level, stage=stage, last_update=last_update)
        return DynamicData()
    except Exception as err:
        raise LHPError(err, "hh_api.py: update_HH()") from err
