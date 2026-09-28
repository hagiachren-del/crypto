"""Per-device bearer tokens from .env (ROUTER_TOKENS=device:token,...)."""

from __future__ import annotations

import logging
import secrets

from fastapi import HTTPException, Request

log = logging.getLogger(__name__)


class Authenticator:
    def __init__(self, tokens: dict[str, str]) -> None:
        """`tokens` maps token -> device_id. Empty means the service runs open."""
        self.tokens = dict(tokens)
        if not self.tokens:
            log.warning(
                "ROUTER_TOKENS is empty: the router accepts requests from anyone who can reach "
                "it. Fine behind Tailscale for a first run; set tokens before exposing it."
            )

    @property
    def required(self) -> bool:
        return bool(self.tokens)

    def device_for(self, token: str | None) -> str | None:
        if not token:
            return None
        for known, device in self.tokens.items():
            if secrets.compare_digest(known, token):
                return device
        return None

    def __call__(self, request: Request) -> str | None:
        """FastAPI dependency: returns the device_id for the token, or None when open."""
        header = request.headers.get("authorization", "")
        token = header[7:].strip() if header.lower().startswith("bearer ") else None
        if token is None:
            token = request.query_params.get("token")  # for <audio src=...> and EventSource
        if not self.required:
            return None
        device = self.device_for(token)
        if device is None:
            raise HTTPException(status_code=401, detail="invalid or missing bearer token")
        return device
