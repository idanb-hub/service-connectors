from __future__ import annotations

import collections.abc
import itertools
import typing

import pydantic

# Not in a type-checking block because Pydantic needs field types at runtime.
from .constants import JobStatus  # noqa: TC001


# Pydantic supports ABCs, not sure why Pyright complains.
class _DictModel(pydantic.BaseModel, collections.abc.Mapping[str, typing.Any]):  # pyright: ignore[reportUnsafeMultipleInheritance]
    """Like `pydantic.BaseModel`, but implements `Mapping` interface.

    Extras are allowed by default. Essentially, this should behave like a
    `TypedDict` with runtime validation.
    """

    model_config = pydantic.ConfigDict(extra="allow")

    # We know it's not None because `extra` is set to "allow".
    __pydantic_extra__: dict[str, typing.Any]  # pyright: ignore[reportIncompatibleVariableOverride]

    @typing.override
    def __getitem__(self, key: str) -> typing.Any:
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key) from None

    @typing.override
    def __iter__(self) -> collections.abc.Iterator[str]:  # pyright: ignore[reportIncompatibleMethodOverride]
        return itertools.chain(
            self.__pydantic_fields__,
            self.__pydantic_extra__,
        )

    @typing.override
    def __len__(self) -> int:
        return len(self.__pydantic_fields__) + len(self.__pydantic_extra__)


class Job(_DictModel):
    status: JobStatus
