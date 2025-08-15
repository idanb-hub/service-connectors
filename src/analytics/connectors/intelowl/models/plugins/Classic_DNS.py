from __future__ import annotations

import typing

from ..base import PluginModel, PluginType


class Classic_DNS(PluginModel, frozen=True):  # noqa: N801
    name: typing.Literal["Classic_DNS"]
    type: typing.Literal[PluginType.ANALYZER]
    # https://github.com/intelowlproject/IntelOwl/blob/v6.4.0/api_app/analyzers_manager/observable_analyzers/dns/dns_resolvers/classic_dns_resolver.py#L26
    report: Report


class Report(typing.TypedDict):
    # https://github.com/intelowlproject/IntelOwl/blob/v6.4.0/api_app/analyzers_manager/observable_analyzers/dns/dns_responses.py#L34
    observable: str
    resolutions: list[ResolutionIP] | list[ResolutionDomainURL]
    timeout: typing.NotRequired[int]


# https://github.com/intelowlproject/IntelOwl/blob/v6.4.0/api_app/analyzers_manager/observable_analyzers/dns/dns_resolvers/classic_dns_resolver.py#L29
type ResolutionIP = str


class ResolutionDomainURL(typing.TypedDict):
    # https://github.com/intelowlproject/IntelOwl/blob/v6.4.0/api_app/analyzers_manager/observable_analyzers/dns/dns_resolvers/classic_dns_resolver.py#L52
    TTL: int
    data: str
    name: str
    type: int
