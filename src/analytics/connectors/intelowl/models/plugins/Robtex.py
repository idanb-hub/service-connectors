from __future__ import annotations

import datetime
import typing

from ..base import PluginModel, PluginType


class Robtex(PluginModel, frozen=True):
    name: typing.Literal["Robtex"]
    type: typing.Literal[PluginType.ANALYZER]
    # https://github.com/intelowlproject/IntelOwl/blob/v6.4.0/api_app/analyzers_manager/observable_analyzers/robtex.py#L22
    report: ReportIP | ReportDomainURL


# https://github.com/intelowlproject/IntelOwl/blob/v6.4.0/api_app/analyzers_manager/observable_analyzers/robtex.py#L23
type ReportIP = list[PDNS_Reverse | IPQuery]


class IPQuery(typing.TypedDict):
    # https://freeapi.robtex.com/api/#ipquery
    status: typing.Literal["ok"] | str  # noqa: PYI051
    pas: list[DNS]
    pash: list[DNS]
    act: list[DNS]
    acth: list[DNS]
    # There are more fields, but only these are explicitly documented.


class DNS(typing.TypedDict):
    o: str
    # Pydantic can validate datetime from Unix timestamp.
    t: datetime.datetime


class PDNS_Reverse(typing.TypedDict):  # noqa: N801
    # https://freeapi.robtex.com/api/#pdns_reverse
    # https://datatracker.ietf.org/doc/html/draft-dulaunoy-dnsop-passive-dns-cof-03
    rrname: str
    rrtype: str
    # NOTE: According to the IETF draft, this should be named `rdata`.
    rrdata: str
    # Pydantic can validate datetime from Unix timestamp.
    time_first: datetime.datetime
    time_last: datetime.datetime
    count: int


# https://github.com/intelowlproject/IntelOwl/blob/v6.4.0/api_app/analyzers_manager/observable_analyzers/robtex.py#L28
type ReportDomainURL = list[PDNS_Forward]


# https://freeapi.robtex.com/api/#pdns_forward
type PDNS_Forward = PDNS_Reverse
