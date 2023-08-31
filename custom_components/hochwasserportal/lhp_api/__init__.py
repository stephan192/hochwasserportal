"""The Länderübergreifendes Hochwasser Portal API."""

from __future__ import annotations
from .api_utils import LHPError
from .bb_api import init_BB, parse_BB
from .be_api import init_BE, parse_BE
from .bw_api import init_BW, parse_BW
from .by_api import init_BY, parse_BY
from .hb_api import init_HB, parse_HB
from .he_api import init_HE, parse_HE
from .hh_api import init_HH, parse_HH
from .mv_api import init_MV, parse_MV
from .ni_api import init_NI, parse_NI
from .nw_api import init_NW, parse_NW
from .rp_api import init_RP, parse_RP
from .sh_api import init_SH, parse_SH
from .sl_api import init_SL, parse_SL
from .sn_api import init_SN, parse_SN
from .st_api import init_ST, parse_ST
from .th_api import init_TH, parse_TH


class HochwasserPortalAPI:
    """API to retrieve the data."""

    def __init__(self, ident) -> None:
        """Initialize the API."""
        self.ident = ident
        self.name = None
        self.level = None
        self.stage = None
        self.flow = None
        self.internal_url = None
        self.url = None
        self.hint = None
        self.stage_levels = [None] * 4
        self.last_update = None
        if len(ident) > 3:
            self.parse_init()
            self.update()
        else:
            raise LHPError(
                "Invalid ident given (ident too short)!", "__init__py: __init__()"
            )

    def parse_init(self):
        """Init data."""
        init_data = None
        if self.ident[0:3] == "BB_":
            init_data = init_BB(self.ident)
        elif self.ident[0:3] == "BE_":
            init_data = init_BE(self.ident)
        elif self.ident[0:3] == "BW_":
            init_data = init_BW(self.ident)
        elif self.ident[0:3] == "BY_":
            init_data = init_BY(self.ident)
        elif self.ident[0:3] == "HB_":
            init_data = init_HB(self.ident)
        elif self.ident[0:3] == "HE_":
            init_data = init_HE(self.ident)
        elif self.ident[0:3] == "HH_":
            init_data = init_HH(self.ident)
        elif self.ident[0:3] == "MV_":
            init_data = init_MV(self.ident)
        elif self.ident[0:3] == "NI_":
            init_data = init_NI(self.ident)
        elif self.ident[0:3] == "NW_":
            init_data = init_NW(self.ident)
        elif self.ident[0:3] == "RP_":
            init_data = init_RP(self.ident)
        elif self.ident[0:3] == "SH_":
            init_data = init_SH(self.ident)
        elif self.ident[0:3] == "SL_":
            init_data = init_SL(self.ident)
        elif self.ident[0:3] == "SN_":
            init_data = init_SN(self.ident)
        elif self.ident[0:3] == "ST_":
            init_data = init_ST(self.ident)
        elif self.ident[0:3] == "TH_":
            init_data = init_TH(self.ident)

        if init_data is not None:
            self.name = getattr(init_data, "name", None)
            if self.name is None:
                raise LHPError(
                    "Invalid ident given (nothing found)!", "__init__.py: parse_init()"
                )
            self.url = getattr(init_data, "url", None)
            self.internal_url = getattr(init_data, "internal_url", None)
            self.hint = getattr(init_data, "hint", None)
            self.stage_levels = getattr(init_data, "stage_levels", [None] * 4)
        else:
            raise LHPError(
                "Invalid ident given (wrong first letters)!",
                "__init__.py: parse_init()",
            )

    def update(self):
        """Update data."""
        cyclic_data = None
        if self.ident[0:3] == "BB_":
            cyclic_data = parse_BB(self.ident)
        elif self.ident[0:3] == "BE_":
            cyclic_data = parse_BE(self.url)
        elif self.ident[0:3] == "BW_":
            cyclic_data = parse_BW(self.ident, self.stage_levels)
        elif self.ident[0:3] == "BY_":
            cyclic_data = parse_BY(self.ident)
        elif self.ident[0:3] == "HB_":
            cyclic_data = parse_HB(self.internal_url, self.stage_levels)
        elif self.ident[0:3] == "HE_":
            cyclic_data = parse_HE(self.internal_url, self.stage_levels)
        elif self.ident[0:3] == "HH_":
            cyclic_data = parse_HH(self.ident)
        elif self.ident[0:3] == "MV_":
            cyclic_data = parse_MV(self.ident)
        elif self.ident[0:3] == "NI_":
            cyclic_data = parse_NI(self.internal_url)
        elif self.ident[0:3] == "NW_":
            cyclic_data = parse_NW(self.internal_url, self.stage_levels)
        elif self.ident[0:3] == "RP_":
            cyclic_data = parse_RP(self.ident, self.stage_levels)
        elif self.ident[0:3] == "SH_":
            cyclic_data = parse_SH(self.ident)
        elif self.ident[0:3] == "SL_":
            cyclic_data = parse_SL(self.ident)
        elif self.ident[0:3] == "SN_":
            cyclic_data = parse_SN(self.ident)
        elif self.ident[0:3] == "ST_":
            cyclic_data = parse_ST(self.internal_url, self.stage_levels)
        elif self.ident[0:3] == "TH_":
            cyclic_data = parse_TH(self.ident)

        if cyclic_data is not None:
            self.last_update = getattr(cyclic_data, "last_update", None)
            self.level = getattr(cyclic_data, "level", None)
            self.stage = getattr(cyclic_data, "stage", None)
            self.flow = getattr(cyclic_data, "flow", None)
        else:
            raise LHPError(
                "Invalid ident given (wrong first letters)!", "__init__.py: update()"
            )
