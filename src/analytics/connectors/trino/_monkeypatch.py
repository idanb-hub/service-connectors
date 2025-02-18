from __future__ import annotations

import typing

import trino

if typing.TYPE_CHECKING:
    from typing import Any


class _TrinoQueryPatched(trino.client.TrinoQuery):
    @typing.override
    def execute(self, *args: Any, **kwargs: Any) -> trino.client.TrinoResult:
        # `TrinoQuery.execute()` blocks until results are ready by repeatedly
        # calling `.fetch()` until it returns non-empty.
        # To make `.execute()` non-blocking, we patch `.fetch()` to return
        # a dummy row when it would have returned empty, so that `.execute()`
        # thinks the results are starting to come in.
        # See the upstream code for context:
        #   https://github.com/trinodb/trino-python-client/blob/0.333.0/trino/client.py#L898

        fetch = self.fetch
        dummy = []
        self.fetch = lambda *args, **kwargs: fetch(*args, **kwargs) or [dummy]

        result = super().execute(*args, **kwargs)

        # Remove the patched `.fetch()` so that the rest is fetched normally.
        del self.fetch

        # Remove the dummy row from the results, if it is there.
        rows = typing.cast("list[list[object]]", result.rows)
        assert rows is not None
        if rows[0] is dummy:
            rows.pop(0)

        return result


_TrinoQueryOriginal = trino.client.TrinoQuery


def make_execute_non_blocking() -> None:
    """Patch `trino.client.TrinoQuery.execute` to make it non-blocking."""
    trino.client.TrinoQuery = _TrinoQueryPatched


def remove_patches() -> None:
    """Remove any previously applied patches."""
    trino.client.TrinoQuery = _TrinoQueryOriginal
