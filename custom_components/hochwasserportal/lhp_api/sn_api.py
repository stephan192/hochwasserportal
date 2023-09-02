"""The Länderübergreifendes Hochwasser Portal API - Functions for Sachsen."""

from __future__ import annotations

from .api_utils import (
    DynamicData,
    LHPError,
    StaticData,
    convert_to_datetime,
    convert_to_float,
    fetch_soup,
)


def init_SN(ident: str) -> StaticData:  # pylint: disable=invalid-name
    """Init data for Sachsen."""
    try:
        # Get data
        soup = fetch_soup(
            "https://www.umwelt.sachsen.de/umwelt/infosysteme"
            + "/hwims/portal/web/wasserstand-uebersicht"
        )
        karte = soup.find_all("div", class_="karteWrapper")[0]
        link = karte.find_all("a", href="wasserstand-pegel-" + ident[3:])[0]
        # Parse data
        name = link.find_next("span", class_="popUpTitleBold").getText().strip()
        url = (
            "https://www.umwelt.sachsen.de/umwelt/infosysteme/hwims/portal/web/"
            + link["href"]
        )
        return StaticData(ident=ident, name=name, url=url)
    except Exception as err:
        raise LHPError(err, "sn_api.py: init_SN()") from err


def update_SN(static_data: StaticData) -> DynamicData:  # pylint: disable=invalid-name
    """Update data for Sachsen."""
    try:
        # Get data
        soup = fetch_soup(
            "https://www.umwelt.sachsen.de/umwelt/infosysteme"
            + "/hwims/portal/web/wasserstand-uebersicht"
        )
        karte = soup.find_all("div", class_="karteWrapper")[0]
        link = karte.find_all("a", href="wasserstand-pegel-" + static_data.ident[3:])[0]
        # Parse data
        if "meldePegel" in link.attrs["class"]:
            stage_colors = {
                "#b38758": 0,
                "#c5e566": 0,
                "#ffeb3b": 1,
                "#fb8a00": 2,
                "#e53835": 3,
                "#d400f9": 4,
            }
            data = link.find_next("div", class_="popUpStatus")
            if (
                "style" in data.attrs
                and isinstance(data.attrs["style"], list)
                and len(data.attrs["style"]) > 0
            ):
                color = data.attrs["style"].split()[-1]
                stage = stage_colors.get(color)
            else:
                stage = None
        else:
            stage = None
        head = link.find_next("span", string="Wasserstand:")
        data = head.find_next("span", class_="popUpValue")
        level = convert_to_float(data.getText().split()[0])
        head = link.find_next("span", string="Durchfluss:")
        data = head.find_next("span", class_="popUpValue")
        flow = convert_to_float(data.getText().split()[0], True)
        head = link.find_next("span", string="Datum:")
        data = head.find_next("span", class_="popUpValue")
        last_update = convert_to_datetime(
            data.getText().strip().split()[0], "%d.%m.%Y%H:%M"
        )
        return DynamicData(level=level, stage=stage, flow=flow, last_update=last_update)
    except Exception as err:
        raise LHPError(err, "sn_api.py: update_SN()") from err
