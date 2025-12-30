"""API client for Intesis Local devices."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import (
    CMD_GET_DP_VALUE,
    CMD_GET_INFO,
    CMD_LOGIN,
    CMD_SET_DP_VALUE,
)

_LOGGER = logging.getLogger(__name__)


class IntesisConnectionError(Exception):
    """Error connecting to Intesis device."""


class IntesisAuthError(Exception):
    """Authentication error with Intesis device."""


class IntesisError(Exception):
    """General Intesis API error."""


class IntesisLocalAPI:
    """API client for Intesis Local devices."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the API client."""
        self._host = host
        self._username = username
        self._password = password
        self._session = session
        self._session_id: str | None = None
        self._session_lock = asyncio.Lock()
        self._retry_count = 0
        self._max_retries = 2

    @property
    def host(self) -> str:
        """Return the host."""
        return self._host

    async def _login(self) -> None:
        """Authenticate with the device."""
        _LOGGER.debug("Logging in to %s", self._host)

        try:
            async with self._session.post(
                f"http://{self._host}/api.cgi",
                json={
                    "command": CMD_LOGIN,
                    "data": {
                        "username": self._username,
                        "password": self._password,
                    },
                },
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    raise IntesisConnectionError(f"HTTP error {resp.status}")

                result = await resp.json()

                if not result.get("success"):
                    error_msg = result.get("error", {}).get("message", "Login failed")
                    raise IntesisAuthError(error_msg)

                self._session_id = result["data"]["id"]["sessionID"]
                _LOGGER.debug("Login successful, session: %s", self._session_id[:8])

        except aiohttp.ClientError as err:
            raise IntesisConnectionError(f"Connection error: {err}") from err

    async def _ensure_session(self) -> None:
        """Ensure we have a valid session."""
        async with self._session_lock:
            if self._session_id is None:
                await self._login()

    async def _request(
        self, command: str, data: dict[str, Any] | None = None, retry: bool = True
    ) -> dict[str, Any]:
        """Make an API request with automatic re-auth on failure."""
        await self._ensure_session()

        payload: dict[str, Any] = {
            "command": command,
            "data": {"sessionID": self._session_id},
        }

        if data:
            payload["data"].update(data)

        try:
            async with self._session.post(
                f"http://{self._host}/api.cgi",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    raise IntesisConnectionError(f"HTTP error {resp.status}")

                result = await resp.json()

                if not result.get("success"):
                    error_code = result.get("error", {}).get("code")
                    error_msg = result.get("error", {}).get("message", "Unknown error")

                    # Auth errors - clear session and retry once
                    if error_code in (1, 5) and retry:
                        _LOGGER.debug("Session expired, re-authenticating")
                        async with self._session_lock:
                            self._session_id = None
                        return await self._request(command, data, retry=False)

                    raise IntesisError(f"API error {error_code}: {error_msg}")

                return result.get("data", {})

        except aiohttp.ClientError as err:
            raise IntesisConnectionError(f"Connection error: {err}") from err

    async def get_info(self) -> dict[str, Any]:
        """Get device information (doesn't require session)."""
        try:
            async with self._session.post(
                f"http://{self._host}/api.cgi",
                json={"command": CMD_GET_INFO},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    raise IntesisConnectionError(f"HTTP error {resp.status}")

                result = await resp.json()

                if not result.get("success"):
                    raise IntesisError("Failed to get device info")

                return result["data"]["info"]

        except aiohttp.ClientError as err:
            raise IntesisConnectionError(f"Connection error: {err}") from err

    async def get_all_datapoints(self) -> list[dict[str, Any]]:
        """Get all datapoint values."""
        result = await self._request(CMD_GET_DP_VALUE, {"uid": "all"})
        return result.get("dpval", [])

    async def set_datapoint(self, uid: int, value: int) -> None:
        """Set a datapoint value."""
        _LOGGER.debug("Setting UID %d to %d", uid, value)
        await self._request(CMD_SET_DP_VALUE, {"uid": uid, "value": value})

    async def validate_connection(self) -> dict[str, Any]:
        """Validate connection and return device info."""
        info = await self.get_info()
        await self._login()  # Also verify credentials work
        return info

    def invalidate_session(self) -> None:
        """Invalidate the current session (force re-login on next request)."""
        self._session_id = None
