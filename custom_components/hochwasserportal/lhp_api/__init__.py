"""The Länderübergreifendes Hochwasser Portal API."""

from __future__ import annotations
from datetime import datetime
from .api_utils import LHPError, StaticData, DynamicData
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


def init_lhp_data(ident: str) -> StaticData:
    """Init LHP API data."""
    static_data = None
    if ident[0:3] == "BB_":
        static_data = init_BB(ident)
    elif ident[0:3] == "BE_":
        static_data = init_BE(ident)
    elif ident[0:3] == "BW_":
        static_data = init_BW(ident)
    elif ident[0:3] == "BY_":
        static_data = init_BY(ident)
    elif ident[0:3] == "HB_":
        static_data = init_HB(ident)
    elif ident[0:3] == "HE_":
        static_data = init_HE(ident)
    elif ident[0:3] == "HH_":
        static_data = init_HH(ident)
    elif ident[0:3] == "MV_":
        static_data = init_MV(ident)
    elif ident[0:3] == "NI_":
        static_data = init_NI(ident)
    elif ident[0:3] == "NW_":
        static_data = init_NW(ident)
    elif ident[0:3] == "RP_":
        static_data = init_RP(ident)
    elif ident[0:3] == "SH_":
        static_data = init_SH(ident)
    elif ident[0:3] == "SL_":
        static_data = init_SL(ident)
    elif ident[0:3] == "SN_":
        static_data = init_SN(ident)
    elif ident[0:3] == "ST_":
        static_data = init_ST(ident)
    elif ident[0:3] == "TH_":
        static_data = init_TH(ident)

    if static_data is not None:
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
    dynamic_data = None
    if static_data.ident[0:3] == "BB_":
        dynamic_data = update_BB(static_data.ident)
    elif static_data.ident[0:3] == "BE_":
        dynamic_data = update_BE(static_data.url)
    elif static_data.ident[0:3] == "BW_":
        dynamic_data = update_BW(static_data.ident, static_data.stage_levels)
    elif static_data.ident[0:3] == "BY_":
        dynamic_data = update_BY(static_data.ident)
    elif static_data.ident[0:3] == "HB_":
        dynamic_data = update_HB(static_data.internal_url, static_data.stage_levels)
    elif static_data.ident[0:3] == "HE_":
        dynamic_data = update_HE(static_data.internal_url, static_data.stage_levels)
    elif static_data.ident[0:3] == "HH_":
        dynamic_data = update_HH(static_data.ident)
    elif static_data.ident[0:3] == "MV_":
        dynamic_data = update_MV(static_data.ident)
    elif static_data.ident[0:3] == "NI_":
        dynamic_data = update_NI(static_data.internal_url)
    elif static_data.ident[0:3] == "NW_":
        dynamic_data = update_NW(static_data.internal_url, static_data.stage_levels)
    elif static_data.ident[0:3] == "RP_":
        dynamic_data = update_RP(static_data.ident, static_data.stage_levels)
    elif static_data.ident[0:3] == "SH_":
        dynamic_data = update_SH(static_data.ident)
    elif static_data.ident[0:3] == "SL_":
        dynamic_data = update_SL(static_data.ident)
    elif static_data.ident[0:3] == "SN_":
        dynamic_data = update_SN(static_data.ident)
    elif static_data.ident[0:3] == "ST_":
        dynamic_data = update_ST(static_data.internal_url, static_data.stage_levels)
    elif static_data.ident[0:3] == "TH_":
        dynamic_data = update_TH(static_data.ident)

    if dynamic_data is not None:
        return dynamic_data
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
