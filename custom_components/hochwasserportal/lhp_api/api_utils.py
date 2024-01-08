"""The Länderübergreifendes Hochwasser Portal API - Utility functions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from requests import get


class LHPError(Exception):
    """Exception occurred while running."""

    def __init__(self, exception: Exception | str, location: str) -> None:
        """Init the error."""
        if isinstance(exception, str):
            super().__init__(f"{location}: {exception}")
        else:
            super().__init__(f"{location}: {exception.__class__.__name__}: {exception}")


@dataclass
class StaticData:
    """Class containing the static data."""

    ident: str
    name: str = None
    internal_url: str = None
    url: str = None
    hint: str = None
    stage_levels: list[float] = None


@dataclass
class DynamicData:
    """Class containing the dynamic data."""

    level: float = None
    stage: int = None
    flow: float = None
    last_update: datetime = None


def fetch_json(url: str, timeout: float = 10.0) -> Any:
    """Fetch data via json."""
    response = get(url=url, timeout=timeout)
    response.raise_for_status()
    json_data = response.json()
    return json_data


def fetch_soup(
    url: str, timeout: float = 10.0, remove_xml: bool = False
) -> BeautifulSoup:
    """Fetch data via soup."""
    response = get(url=url, timeout=timeout)
    # Override encoding by real educated guess (required for e.g. SH)
    response.encoding = response.apparent_encoding
    response.raise_for_status()
    if remove_xml and (
        (response.text.find('<?xml version="1.0" encoding="ISO-8859-15" ?>')) == 0
    ):
        text = response.text[response.text.find("<!DOCTYPE html>") :]
        soup = BeautifulSoup(text, "lxml")
    else:
        soup = BeautifulSoup(response.text, "lxml")
    return soup


def fetch_text(url: str, timeout: float = 10.0, forced_encoding: str = None) -> str:
    """Fetch data via text."""
    response = get(url=url, timeout=timeout)
    if forced_encoding is not None:
        response.encoding = forced_encoding
    else:
        # Override encoding by real educated guess (required for e.g. BW)
        response.encoding = response.apparent_encoding
    response.raise_for_status()
    return response.text


def calc_stage(level: float, stage_levels: list[float]) -> int:
    """Calc stage from level and stage levels."""
    if (level is None) or all(sl is None for sl in stage_levels):
        return None
    if (stage_levels[3] is not None) and (level > stage_levels[3]):
        return 4
    if (stage_levels[2] is not None) and (level > stage_levels[2]):
        return 3
    if (stage_levels[1] is not None) and (level > stage_levels[1]):
        return 2
    if (stage_levels[0] is not None) and (level > stage_levels[0]):
        return 1
    return 0


def convert_to_int(value: str) -> int:
    """Convert value to int."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def convert_to_float(value: str, _replace: bool = False) -> float:
    """Convert value to float."""
    if _replace:
        value = value.replace(",", ".")
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def convert_to_datetime(value: str, _format: str) -> datetime:
    """Convert value to datetime."""
    try:
        if _format == "iso":
            dt = datetime.fromisoformat(value)
        else:
            dt = datetime.strptime(value, _format)
        # Set timezone if not yet set
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("Europe/Berlin"))
        # Convert datetime to UTC
        dt_utc = dt.astimezone(UTC)
        return dt_utc
    except (TypeError, ValueError):
        return None
