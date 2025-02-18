from __future__ import annotations

import os
import typing

import dacite

if typing.TYPE_CHECKING:
    from _typeshed import DataclassInstance


def fromenv[T: DataclassInstance](dataclass: type[T], prefix: str) -> T:
    """Create a dataclass instance from environment variables."""
    return dacite.from_dict(
        dataclass,
        os.environ,
        dacite.Config(
            cast=[bool, int, float],
            convert_key=lambda key: f"{prefix}{key.upper()}",
        ),
    )
