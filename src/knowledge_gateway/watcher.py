from __future__ import annotations

from pathlib import Path
import time
from typing import Callable


class PollingWatcher:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.snapshot = self._take_snapshot()

    def _take_snapshot(self) -> dict[str, float]:
        return {
            path.relative_to(self.root).as_posix(): path.stat().st_mtime
            for path in self.root.rglob("*.md")
        }

    def poll_changes(self) -> list[str]:
        current = self._take_snapshot()
        changed = [
            path
            for path, modified_time in current.items()
            if path not in self.snapshot or self.snapshot[path] != modified_time
        ]
        changed.extend(path for path in self.snapshot if path not in current)
        self.snapshot = current
        return sorted(set(changed))

    def watch_forever(self, callback: Callable[[list[str]], None], interval: float = 1.0) -> None:
        while True:
            changes = self.poll_changes()
            if changes:
                callback(changes)
            time.sleep(interval)

