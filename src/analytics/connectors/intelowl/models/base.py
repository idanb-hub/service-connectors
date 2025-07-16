from __future__ import annotations

import collections.abc
import itertools
import typing

import pydantic
from pydantic_core import core_schema

from .constants import PluginType


# Pydantic supports ABCs, not sure why Pyright complains.
class DictModel(  # pyright: ignore[reportUnsafeMultipleInheritance]
    pydantic.BaseModel,
    collections.abc.Mapping[str, typing.Any],
    frozen=True,
):
    """Like `pydantic.BaseModel`, but implements `Mapping` interface.

    Extras are allowed by default. Essentially, this should behave like a
    `TypedDict` with runtime validation.
    """

    # This class allows us to add models incrementally, without affecting
    # client code. We can simply return an unvalidated dict when we don't
    # have an appropriate model, and later add validation using a model
    # derived from this class.

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


class PluginModel(DictModel, frozen=True):
    name: str
    type: PluginType


class PluginList(list[dict[str, typing.Any]]):
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: typing.Any,
        handler: pydantic.GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls,
            handler(list[dict[str, typing.Any]]),
        )

    @typing.overload
    def get[T: PluginModel](self, model: type[T], /) -> T | None: ...

    @typing.overload
    def get(self, name: str, /) -> dict[str, typing.Any] | None: ...

    def get[T: PluginModel](
        self,
        name_or_model: str | type[T],
        /,
    ) -> T | dict[str, typing.Any] | None:
        if isinstance(name_or_model, str):
            return self._get_dict(name=name_or_model)

        return self._get_model(model=name_or_model)

    def _get_model[T: PluginModel](self, model: type[T]) -> T | None:
        names = _get_literal_values(model.model_fields["name"].annotation)
        types = _get_literal_values(model.model_fields["type"].annotation)
        for plugin in self:
            if plugin["name"] in names and plugin["type"] in types:
                return model.model_validate(plugin)
        return None

    def _get_dict(self, name: str) -> dict[str, typing.Any] | None:
        for plugin in self:
            if plugin.get("name") == name:
                return plugin
        return None


def _get_literal_values(annotation: type | None) -> tuple[str, ...]:
    # Doesn't work with unions or type aliases, but we don't need that.

    if typing.get_origin(annotation) is not typing.Literal:
        errmsg = f"{annotation} is not {typing.Literal}"
        raise TypeError(errmsg)

    return typing.get_args(annotation)
