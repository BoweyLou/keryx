from __future__ import annotations

from enum import Enum


class WritePolicyError(RuntimeError):
    """Raised when a write violates policy."""


class WriteClass(str, Enum):
    CLASS_A = "class-a"
    CLASS_B = "class-b"
    CLASS_C = "class-c"


class WritePolicyManager:
    def __init__(self, allow_class_c: bool, allowed_targets: list[str]) -> None:
        self.allow_class_c = allow_class_c
        self.allowed_targets = allowed_targets

    def assert_allowed(self, *, write_class: WriteClass, note_path: str) -> None:
        if write_class is WriteClass.CLASS_C and not self.allow_class_c:
            raise WritePolicyError("Class C mutations are disabled by default.")
        if not any(note_path.startswith(prefix) for prefix in self.allowed_targets):
            raise WritePolicyError(f"Writes to '{note_path}' are outside configured allowed targets.")

