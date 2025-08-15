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
    """Base class for models of IntelOwl plugins.

    Subclasses are required to define two literal fields: `name` and `type`.
    In every subclass, literal values from type annotations on literal fields
    are made accessible as class variables (named same as the fields).
    """

    REQUIRED_LITERAL_FIELDS: typing.ClassVar[tuple[str, ...]] = ("name", "type")

    name: str
    type: PluginType

    @classmethod
    @typing.override
    def __pydantic_init_subclass__(cls, **kwargs: typing.Any) -> None:
        super().__pydantic_init_subclass__(**kwargs)

        # Ensure subclass defines the required literal fields.
        # NOTE: Pyright enforces that the literal values have compatible types.
        for name in PluginModel.REQUIRED_LITERAL_FIELDS:
            cls_field_type = cls.model_fields[name].annotation
            if typing.get_origin(cls_field_type) is not typing.Literal:
                expected_type = PluginModel.model_fields[name].annotation
                errmsg = (
                    f"invalid type annotation on field '{name}', "
                    f"expected {expected_type.__qualname__} literal"
                )
                raise TypeError(errmsg)

        # Make values of literal fields accessible as class variables.
        for name, field in cls.model_fields.items():
            if typing.get_origin(field.annotation) is not typing.Literal:
                continue

            values = typing.get_args(field.annotation)
            if not values:
                continue

            setattr(cls, name, values[0])


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
        for plugin in self:
            if plugin["name"] == model.name and plugin["type"] == model.type:
                return model.model_validate(plugin)
        return None

    def _get_dict(self, name: str) -> dict[str, typing.Any] | None:
        for plugin in self:
            if plugin.get("name") == name:
                return plugin
        return None
