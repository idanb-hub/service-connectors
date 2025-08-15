from __future__ import annotations

import typing

from ..base import PluginModel, PluginType


class WhoIs_RipeDB_Search(PluginModel, frozen=True):  # noqa: N801
    name: typing.Literal["WhoIs_RipeDB_Search"]
    type: typing.Literal[PluginType.ANALYZER]
    # https://github.com/intelowlproject/IntelOwl/blob/v6.4.0/api_app/analyzers_manager/observable_analyzers/whoisripe.py#L13
    report: Report


class Report(typing.TypedDict):
    objects: Objects


class Objects(typing.TypedDict):
    object: list[Object]


class Object(typing.TypedDict):
    link: Link
    attributes: Attributes


class Link(typing.TypedDict):
    href: str
    type: str


class Attributes(typing.TypedDict):
    attribute: list[Attribute]


class Attribute(typing.TypedDict):
    name: str
    value: str
    comment: typing.NotRequired[str]
