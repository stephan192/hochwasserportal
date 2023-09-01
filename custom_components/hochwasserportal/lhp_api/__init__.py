"""The Länderübergreifendes Hochwasser Portal API."""

from __future__ import annotations

from datetime import datetime
from types import FunctionType
from typing import Final

from .api_utils import DynamicData, LHPError, StaticData
from .bb_api import init_BB, update_BB
from .be_api import init_BE, update_BE
from .bw_api import init_BW, update_BW
from .by_api import init_BY, update_BY
from .hb_api import init_HB, update_HB
from .he_api import init_HE, update_HE
from .hh_api import init_HH, update_HH
from .mv_api import init_MV, update_MV
from .ni_api import init_NI, update_NI
from .nw_api import init_NW, update_NW
from .rp_api import init_RP, update_RP
from .sh_api import init_SH, update_SH
from .sl_api import init_SL, update_SL
from .sn_api import init_SN, update_SN
from .st_api import init_ST, update_ST
from .th_api import init_TH, update_TH

FUNCTION_DICT: Final[dict[str, dict[str, FunctionType]]] = {
    "BB": {"init": init_BB, "update": update_BB},
    "BE": {"init": init_BE, "update": update_BE},
    "BW": {"init": init_BW, "update": update_BW},
    "BY": {"init": init_BY, "update": update_BY},
    "HB": {"init": init_HB, "update": update_HB},
    "HE": {"init": init_HE, "update": update_HE},
    "HH": {"init": init_HH, "update": update_HH},
    "MV": {"init": init_MV, "update": update_MV},
    "NI": {"init": init_NI, "update": update_NI},
    "NW": {"init": init_NW, "update": update_NW},
    "RP": {"init": init_RP, "update": update_RP},
    "SH": {"init": init_SH, "update": update_SH},
    "SL": {"init": init_SL, "update": update_SL},
    "SN": {"init": init_SN, "update": update_SN},
    "ST": {"init": init_ST, "update": update_ST},
    "TH": {"init": init_TH, "update": update_TH},
}


def init_lhp_data(ident: str) -> StaticData:
    """Init LHP API data."""
    prefix = ident[:2]
    if prefix in FUNCTION_DICT:
        static_data = FUNCTION_DICT[prefix]["init"](ident)
        if static_data.name is None:
            raise LHPError(
                "Invalid ident given (nothing found)!", "__init__.py: init_lhp_data()"
            )
        return static_data
    raise LHPError(
        "Invalid ident given (wrong first letters)!",
        "__init__.py: init_lhp_data()",
    )


def update_lhp_data(static_data: StaticData) -> DynamicData:
    """Update data."""
    prefix = static_data.ident[:2]
    if prefix in FUNCTION_DICT:
        return FUNCTION_DICT[prefix]["update"](static_data)
    raise LHPError(
        "Invalid ident given (wrong first letters)!", "__init__.py: update_lhp_data()"
    )


class HochwasserPortalAPI:
    """API to retrieve the data."""

    def __init__(self, ident: str) -> None:
        """Initialize the API."""
        if len(ident) > 3:
            self.static_data = init_lhp_data(ident)
            self.dynamic_data = update_lhp_data(self.static_data)
        else:
            self.static_data = StaticData(ident=ident)
            self.dynamic_data = DynamicData()
            raise LHPError(
                "Invalid ident given (ident too short)!", "__init__py: __init__()"
            )

    def update(self):
        """Update data."""
        self.dynamic_data = update_lhp_data(self.static_data)

    def __repr__(self) -> str:
        """Return representation."""
        data_dict = {
            "static_data": vars(self.static_data),
            "dynamic_data": vars(self.dynamic_data),
        }
        return str(data_dict)

    @property
    def ident(self) -> str:
        """Return ident."""
        return self.static_data.ident

    @property
    def name(self) -> str:
        """Return name."""
        return self.static_data.name

    @property
    def url(self) -> str:
        """Return url."""
        return self.static_data.url

    @property
    def hint(self) -> str:
        """Return hint."""
        return self.static_data.hint

    @property
    def level(self) -> float:
        """Return level."""
        return self.dynamic_data.level

    @property
    def stage(self) -> int:
        """Return stage."""
        return self.dynamic_data.stage

    @property
    def flow(self) -> float:
        """Return flow."""
        return self.dynamic_data.flow

    @property
    def last_update(self) -> datetime:
        """Return last_update."""
        return self.dynamic_data.last_update
