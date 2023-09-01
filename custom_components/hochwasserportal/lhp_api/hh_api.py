"""The Länderübergreifendes Hochwasser Portal API - Functions for Hamburg."""

from __future__ import annotations

from datetime import datetime

from .api_utils import DynamicData, LHPError, StaticData, fetch_soup


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
        last_update = None
        if len(spans) == 8:
            text = div.getText()
            try:
                level = float(
                    text[
                        text.find("Wasserstand")
                        + 11 : text.find("[NHN\u00A0+/-\u00A0cm]")
                    ]
                    .replace(".", "")
                    .strip()
                )
            except:
                level = None
            try:
                last_update = datetime.strptime(
                    text[
                        text.find("\u00A0\u00A0\u00A0 um") + 6 : text.find("Trend")
                    ].strip(),
                    "%d.%m.%Y %H:%M",
                )
            except:
                last_update = None
            try:
                stage_in = int(spans[7].attrs["class"][-1].split("_")[-1])
                if stage_in == 0:
                    stage = 0
                elif stage_in == 1:
                    stage = 1
                elif stage_in == 2:
                    stage = 3
                else:
                    stage = None
            except:
                stage = None
        return DynamicData(level=level, stage=stage, last_update=last_update)
    except Exception as err:
        raise LHPError(err, "hh_api.py: update_HH()") from err
