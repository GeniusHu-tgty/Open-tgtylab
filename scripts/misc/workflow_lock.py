from __future__ import annotations

import os
import threading
import time
import weakref
from pathlib import Path


_LOCKS_GUARD = threading.Lock()
_PROCESS_LOCKS = weakref.WeakValueDictionary()
_THREAD_STATE = threading.local()


def _platform_name() -> str:
    return os.name


def _process_lock(key: str) -> threading.RLock:
    with _LOCKS_GUARD:
        return _PROCESS_LOCKS.setdefault(key, threading.RLock())


def _lock_handle(handle) -> None:
    handle.seek(0)
    if _platform_name() == "nt":
        import msvcrt

        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        return

    import fcntl

    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock_handle(handle) -> None:
    handle.seek(0)
    if _platform_name() == "nt":
        import msvcrt

        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        return

    import fcntl

    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


class WorkflowFileLock:
    """Re-entrant process and OS-level lock for one workflow directory."""

    def __init__(self, path: str | Path, timeout: float = 10.0):
        self.path = Path(path).resolve()
        self.timeout = float(timeout)
        self._key = str(self.path)
        self._process_lock = _process_lock(self._key)
        self._enter_count = 0

    def __enter__(self) -> "WorkflowFileLock":
        deadline = time.monotonic() + self.timeout
        remaining = max(0.0, deadline - time.monotonic())
        if not self._process_lock.acquire(timeout=remaining):
            raise TimeoutError(f"workflow lock timeout: {self.path}")
        self._enter_count += 1
        try:
            active = getattr(_THREAD_STATE, "active", None)
            if active is None:
                active = {}
                _THREAD_STATE.active = active
            if self._key in active:
                active[self._key]["depth"] += 1
                return self

            self.path.parent.mkdir(parents=True, exist_ok=True)
            handle = self.path.open("a+b")
            try:
                if handle.seek(0, os.SEEK_END) == 0:
                    handle.write(b"\0")
                    handle.flush()
                    os.fsync(handle.fileno())

                while True:
                    try:
                        _lock_handle(handle)
                        active[self._key] = {"handle": handle, "depth": 1}
                        return self
                    except OSError as exc:
                        if time.monotonic() >= deadline:
                            raise TimeoutError(
                                f"workflow lock timeout: {self.path}"
                            ) from exc
                        time.sleep(
                            min(
                                0.01,
                                max(0.0, deadline - time.monotonic()),
                            )
                        )
            except BaseException:
                handle.close()
                raise
        except BaseException:
            self._process_lock.release()
            self._enter_count -= 1
            raise

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._enter_count == 0:
            return
        try:
            active = getattr(_THREAD_STATE, "active", {})
            entry = active.get(self._key)
            if entry is not None:
                entry["depth"] -= 1
                if entry["depth"] == 0:
                    handle = entry["handle"]
                    try:
                        _unlock_handle(handle)
                    finally:
                        handle.close()
                        del active[self._key]
        finally:
            self._process_lock.release()
            self._enter_count -= 1
