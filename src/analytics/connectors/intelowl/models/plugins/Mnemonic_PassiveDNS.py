from __future__ import annotations

import datetime
import typing

from ..base import PluginModel, PluginType


class Mnemonic_PassiveDNS(PluginModel, frozen=True):  # noqa: N801
    name: typing.Literal["Mnemonic_PassiveDNS"]
    type: typing.Literal[PluginType.ANALYZER]
    # https://github.com/intelowlproject/IntelOwl/blob/v6.4.0/api_app/analyzers_manager/observable_analyzers/mnemonic_pdns.py#L22
    # https://portal.mnemonic.no/spa/swagger?apistatus=PUBLIC&module=pdns#operations-tag-pdns\/v3
    report: list[PassiveDNS_CommonOutputFormat_v6]


class PassiveDNS_CommonOutputFormat_v6(typing.TypedDict):  # noqa: N801
    # https://www.ietf.org/archive/id/draft-dulaunoy-dnsop-passive-dns-cof-06.txt
    rrname: str
    rrtype: str
    rdata: str
    # Pydantic can validate these from Unix time.
    time_first: datetime.datetime
    time_last: datetime.datetime
    count: int
