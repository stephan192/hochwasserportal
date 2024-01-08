"""The Länderübergreifendes Hochwasser Portal API - Functions for Schleswig-Holstein."""

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


def init_SH(ident: str) -> StaticData:  # pylint: disable=invalid-name
    """Init data for Schleswig-Holstein."""
    try:
        # Get data
        soup = fetch_soup("https://hsi-sh.de")
        search_string = "dialogheader-" + ident[3:]
        headings = soup.find_all("h1", id=search_string)
        # Parse data
        heading = headings[0]
        heading_text = heading.getText().split()
        name = " ".join(heading_text[0 : len(heading_text) - 2])
        d_list = heading.find_next()
        for element in d_list:
            if (
                element.name == "dd"
                and element.attrs["class"][0] == "tooltip-content__gewaesser"
            ):
                name += " / " + element.getText()
        paragraph = heading.find_next("p", class_="tooltip-content__link")
        link = paragraph.find_next("a")
        if link["href"][0] == ".":
            url = "https://hsi-sh.de/" + link["href"][2:]
        else:
            url = link["href"]
        return StaticData(ident=ident, name=name, url=url)
    except Exception as err:
        raise LHPError(err, "sh_api.py: init_SH()") from err


def update_SH(static_data: StaticData) -> DynamicData:  # pylint: disable=invalid-name
    """Update data for Schleswig-Holstein."""
    level = None
    flow = None
    stage = None
    last_update = None
    try:
        # Get data
        soup = fetch_soup("https://hsi-sh.de")
        search_string = "dialogheader-" + static_data.ident[3:]
        headings = soup.find_all("h1", id=search_string)
        # Parse data
        heading = headings[0]
        if heading.attrs["class"][1].count("_") == 3:
            stage = convert_to_int(heading.attrs["class"][1].split("_")[-1])
            if stage is not None:
                stage = stage - 5
                stage = max(stage, 0)
        d_list = heading.find_next()
        for element in d_list:
            if (
                element.name == "dd"
                and element.attrs["class"][0] == "tooltip-content__w"
            ):
                element_text = element.getText().split()
                if element_text[1] == "cm":
                    level = convert_to_float(element_text[0], True)
                    if element_text[4] == "(MEZ)":
                        last_update = convert_to_datetime(
                            element_text[2] + element_text[3] + "+0100",
                            "%d.%m.%Y%H:%M%z",
                        )
                    elif element_text[4] == "(MESZ)":
                        last_update = convert_to_datetime(
                            element_text[2] + element_text[3] + "+0200",
                            "%d.%m.%Y%H:%M%z",
                        )
                    else:
                        last_update = convert_to_datetime(
                            element_text[2] + element_text[3], "%d.%m.%Y%H:%M"
                        )
            if (
                element.name == "dd"
                and element.attrs["class"][0] == "tooltip-content__q"
            ):
                element_text = element.getText().split()
                if element_text[1] == "m3/s":
                    flow = convert_to_float(element_text[0], True)
        return DynamicData(level=level, stage=stage, flow=flow, last_update=last_update)
    except Exception as err:
        raise LHPError(err, "sh_api.py: update_SH()") from err
