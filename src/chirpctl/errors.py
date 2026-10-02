"""User-visible transfer errors."""

from __future__ import annotations


class RadioTransferError(Exception):
    def __init__(
        self,
        message: str,
        *,
        phase: str | None = None,
        port: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        self.phase = phase
        self.port = port
        self.cause = cause
        parts = [message]
        if phase:
            parts.append(f"phase={phase}")
        if port:
            parts.append(f"port={port}")
        if cause and str(cause) not in message:
            parts.append(f"cause={cause}")
        super().__init__("; ".join(parts))
