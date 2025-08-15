from __future__ import annotations

import typing

from ..base import PluginModel, PluginType


class IPApi(PluginModel, frozen=True):
    name: typing.Literal["IPApi"]
    type: typing.Literal[PluginType.ANALYZER]
    report: Report


class Report(typing.TypedDict):
    # https://github.com/intelowlproject/IntelOwl/blob/v6.4.0/api_app/analyzers_manager/observable_analyzers/ipapi.py#L35
    ip_info: list[IPInfo]
    dns_info: DNSInfo


# Can't use the class syntax because some keys aren't valid Python identifiers.
IPInfo = typing.TypedDict(
    "IPInfo",
    {
        # https://ip-api.com/docs/api:batch#:~:text=Returned%20data
        "status": typing.Literal["success", "fail"],
        "message": str,
        "continent": str,
        "continentCode": str,
        "country": str,
        "countryCode": str,
        "region": str,
        "regionName": str,
        "city": str,
        "district": str,
        "zip": str,
        "lat": float,
        "lon": float,
        "timezone": str,
        "offset": int,
        "currency": str,
        "isp": str,
        "org": str,
        "as": str,  # Python keyword :/
        "asname": str,
        "mobile": bool,
        "proxy": bool,
        "hosting": bool,
        "query": str,
    },
    total=False,
)


class DNSInfo(typing.TypedDict):
    # https://ip-api.com/docs/dns
    dns: IPApiDNS
    edns: typing.NotRequired[IPApiDNS]


class IPApiDNS(typing.TypedDict):
    # https://ip-api.com/docs/dns
    ip: str
    geo: str
