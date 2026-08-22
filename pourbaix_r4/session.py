"""Result lifecycle that prevents stale or failed calculations from exporting."""

from __future__ import annotations

from pourbaix_r4.models import ResultSnapshot


class CalculationSession:
    def __init__(self) -> None:
        self._snapshot: ResultSnapshot | None = None
        self._is_stale = False
        self._last_error: Exception | None = None

    @property
    def snapshot(self) -> ResultSnapshot | None:
        return self._snapshot

    @property
    def exportable_snapshot(self) -> ResultSnapshot | None:
        return None if self._is_stale else self._snapshot

    @property
    def last_error(self) -> Exception | None:
        return self._last_error

    def replace_success(self, snapshot: ResultSnapshot) -> None:
        self._snapshot = snapshot
        self._is_stale = False
        self._last_error = None

    def invalidate_for_input_change(self) -> None:
        if self._snapshot is not None:
            self._is_stale = True

    def replace_failure(self, error: Exception) -> None:
        self._snapshot = None
        self._is_stale = True
        self._last_error = error
