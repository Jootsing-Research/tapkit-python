"""Main TapKitClient class."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Literal

import httpx

from .exceptions import TapKitError
from .models import Job, JobStatus, Status
from .phone import Phone


class TapKitClient:
    """Client for the TapKit API.

    The client provides multiple ways to interact with phones:

    1. Single phone (simplest):
        client = TapKitClient()
        phone = client.get_phone()  # Only works with exactly one phone
        phone.tap(phone.screen.center)

    2. Multiple phones by name:
        phone_a = client.phone("iPhone 15 Pro")
        phone_b = client.phone("iPhone 14")
        phone_a.tap((100, 200))

    3. Set a default phone:
        client.use_phone("iPhone 15 Pro")
        client.tap((100, 200))  # Uses iPhone 15 Pro

    4. Explicit phone_id (legacy):
        client.tap((100, 200), phone_id="uuid-here")
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 65.0,
    ):
        """Initialize the client.

        Args:
            api_key: API key for authentication. Defaults to TAPKIT_API_KEY env var.
            base_url: Base URL of the TapKit server. Defaults to TAPKIT_BASE_URL env var,
                      or https://api.tapkit.ai/v1 if not set.
            timeout: Request timeout in seconds.
        """
        self.api_key = api_key or os.environ.get("TAPKIT_API_KEY")
        if not self.api_key:
            raise ValueError("API key required. Set TAPKIT_API_KEY or pass api_key.")

        self.base_url = (base_url or os.environ.get("TAPKIT_BASE_URL") or "https://api.tapkit.ai/v1").rstrip("/")
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"X-API-Key": self.api_key},
            timeout=timeout,
        )
        self._default_phone_id: str | None = None
        self._phones_cache: list[Phone] | None = None

    def close(self):
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # === Internal HTTP methods ===

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Make an HTTP request."""
        response = self._client.request(method, path, **kwargs)
        response.raise_for_status()
        return response

    def _action_request(self, method: str, path: str, **kwargs) -> Job:
        """Make an action request and return Job."""
        response = self._request(method, path, **kwargs)
        data = response.json()
        job = Job(
            id=data["id"],
            status=JobStatus(data["status"]),
            result=data.get("result"),
            created_at=datetime.fromisoformat(data["created_at"]),
            completed_at=(
                datetime.fromisoformat(data["completed_at"])
                if data.get("completed_at")
                else None
            ),
        )
        if job.status == JobStatus.FAILED:
            error_msg = "Action failed"
            if job.result and "error" in job.result:
                error_msg = job.result["error"]
            raise RuntimeError(f"{error_msg} (job_id: {job.id})")
        return job

    # === Phone access ===

    def list_phones(self) -> list[Phone]:
        """List all phones for the org.

        Returns:
            List of Phone objects with dimensions loaded.
        """
        resp = self._request("GET", "/phones")
        phones_data = resp.json()

        phones = []
        for p in phones_data:
            # Fetch dimensions for each phone
            try:
                info_resp = self._request("GET", f"/phones/{p['id']}/info")
                info = info_resp.json()
                width = info.get("width", 0)
                height = info.get("height", 0)
            except httpx.HTTPStatusError:
                # Phone might not be connected, use 0 dimensions
                width = 0
                height = 0

            phone = Phone(
                id=p["id"],
                name=p["name"],
                unique_id=p["unique_id"],
                width=width,
                height=height,
                client=self,
            )
            phones.append(phone)

        self._phones_cache = phones
        return phones

    def phone(self, name_or_id: str) -> Phone:
        """Get a phone by name or ID.

        Args:
            name_or_id: Phone name (e.g., "iPhone 15") or UUID.

        Returns:
            Phone object.

        Raises:
            TapKitError: If phone not found.

        Examples:
            phone = client.phone("iPhone 15")
            phone = client.phone("uuid-here")
        """
        phones = self.list_phones()
        for p in phones:
            if p.id == name_or_id or p.name == name_or_id:
                return p
        raise TapKitError(f"Phone not found: {name_or_id}")

    def get_phone(self) -> Phone:
        """Get the phone (only works if exactly one phone exists).

        This is the simplest way to get a phone when your org has only one device.

        Returns:
            The single Phone object.

        Raises:
            TapKitError: If zero or multiple phones exist.

        Examples:
            phone = client.get_phone()
            phone.tap(phone.screen.center)
        """
        phones = self.list_phones()
        if len(phones) == 0:
            raise TapKitError("No phones registered")
        if len(phones) > 1:
            raise TapKitError(
                f"Multiple phones found ({len(phones)}). "
                "Use client.phone('name') or client.use_phone('name') to specify."
            )
        return phones[0]

    def use_phone(self, name_or_id: str) -> None:
        """Set the default phone for this client session.

        After calling this, client-level action methods will use this phone.

        Args:
            name_or_id: Phone name or UUID.

        Examples:
            client.use_phone("iPhone 15 Pro")
            client.tap((100, 200))  # Uses iPhone 15 Pro
        """
        phone = self.phone(name_or_id)
        self._default_phone_id = phone.id

    def _resolve_phone_id(self, phone_id: str | None = None) -> str:
        """Resolve which phone to use based on precedence.

        Precedence:
        1. Explicit phone_id passed to method
        2. Client default (set via use_phone)
        3. Auto-select if exactly one phone exists
        4. Error if ambiguous

        Args:
            phone_id: Explicitly passed phone_id.

        Returns:
            Resolved phone ID.

        Raises:
            TapKitError: If unable to resolve.
        """
        # 1. Explicit phone_id
        if phone_id:
            return phone_id

        # 2. Client default
        if self._default_phone_id:
            return self._default_phone_id

        # 3. Auto-select if exactly one phone
        phones = self.list_phones()
        if len(phones) == 1:
            return phones[0].id

        # 4. Error
        if len(phones) == 0:
            raise TapKitError("No phones registered")
        raise TapKitError(
            f"Multiple phones found ({len(phones)}). "
            "Use client.use_phone(), client.phone(), or pass phone_id explicitly."
        )

    def _get_phone_by_id(self, phone_id: str) -> Phone:
        """Get a Phone object by ID from cache or fetch."""
        if self._phones_cache:
            for p in self._phones_cache:
                if p.id == phone_id:
                    return p
        # Fetch if not in cache
        phones = self.list_phones()
        for p in phones:
            if p.id == phone_id:
                return p
        raise TapKitError(f"Phone not found: {phone_id}")

    # === Status ===

    def status(self) -> Status:
        """Get system status."""
        resp = self._request("GET", "/status")
        data = resp.json()
        return Status(
            mac_app_running=data["mac_app_running"],
            phone_connected=data["phone_connected"],
            phone_name=data.get("phone_name"),
            switch_control_enabled=data["switch_control_enabled"],
            screen_locked=data["screen_locked"],
            streaming=data["streaming"],
        )

    def get_job(self, job_id: str) -> Job:
        """Get job status."""
        resp = self._request("GET", f"/jobs/{job_id}")
        data = resp.json()
        return Job(
            id=data["id"],
            status=JobStatus(data["status"]),
            result=data.get("result"),
            created_at=datetime.fromisoformat(data["created_at"]),
            completed_at=(
                datetime.fromisoformat(data["completed_at"])
                if data.get("completed_at")
                else None
            ),
        )

    # === Client-level Actions (use phone resolution) ===

    def screenshot(self, phone_id: str | None = None) -> bytes:
        """Capture and return a screenshot as PNG bytes.

        Args:
            phone_id: Phone ID (optional if using default or single phone).

        Returns:
            PNG image data as bytes.
        """
        pid = self._resolve_phone_id(phone_id)
        resp = self._request("GET", f"/phones/{pid}/screenshot")
        return resp.content

    # === Gesture Actions ===

    def tap(self, point, phone_id: str | None = None) -> Job:
        """Tap at a point.

        Args:
            point: Anything that unpacks to (x, y).
            phone_id: Phone ID (optional).
        """
        pid = self._resolve_phone_id(phone_id)
        x, y = point
        return self._action_request("POST", f"/phones/{pid}/tap", json={"x": x, "y": y})

    def tap_with_delays(
        self, x_delay: float, y_delay: float, phone_id: str | None = None
    ) -> Job:
        """Tap using raw scan delay times instead of coordinates."""
        pid = self._resolve_phone_id(phone_id)
        return self._action_request(
            "POST",
            f"/phones/{pid}/tap-with-delays",
            json={"x_delay": x_delay, "y_delay": y_delay},
        )

    def double_tap(self, target, phone_id: str | None = None) -> Job:
        """Double tap at a point or described element.

        Args:
            target: Either a point (unpacks to x, y) or a string selector.
            phone_id: Phone ID (optional).
        """
        pid = self._resolve_phone_id(phone_id)
        if isinstance(target, str):
            return self._action_request(
                "POST", f"/phones/{pid}/double-tap/select", json={"selector": target}
            )
        x, y = target
        return self._action_request(
            "POST", f"/phones/{pid}/double-tap", json={"x": x, "y": y}
        )

    def hold(
        self, target, duration_ms: int = 1000, phone_id: str | None = None
    ) -> Job:
        """Hold (long press) at a point or described element.

        Args:
            target: Either a point (unpacks to x, y) or a string selector.
            duration_ms: Hold duration in milliseconds.
            phone_id: Phone ID (optional).
        """
        pid = self._resolve_phone_id(phone_id)
        if isinstance(target, str):
            return self._action_request(
                "POST",
                f"/phones/{pid}/tap-and-hold/select",
                json={"selector": target, "duration_ms": duration_ms},
            )
        x, y = target
        return self._action_request(
            "POST",
            f"/phones/{pid}/tap-and-hold",
            json={"x": x, "y": y, "duration_ms": duration_ms},
        )

    def flick(
        self,
        target,
        direction: Literal["up", "down", "left", "right"],
        phone_id: str | None = None,
    ) -> Job:
        """Flick gesture from a point or described element.

        Args:
            target: Either a point (unpacks to x, y) or a string selector.
            direction: Flick direction.
            phone_id: Phone ID (optional).
        """
        pid = self._resolve_phone_id(phone_id)
        if isinstance(target, str):
            return self._action_request(
                "POST",
                f"/phones/{pid}/flick/select",
                json={"selector": target, "direction": direction},
            )
        x, y = target
        return self._action_request(
            "POST",
            f"/phones/{pid}/flick",
            json={"x": x, "y": y, "direction": direction},
        )

    def pan(
        self,
        point,
        direction: Literal["up", "down", "left", "right"],
        duration_ms: int = 500,
        phone_id: str | None = None,
    ) -> Job:
        """Pan gesture."""
        pid = self._resolve_phone_id(phone_id)
        x, y = point
        return self._action_request(
            "POST",
            f"/phones/{pid}/pan",
            json={"x": x, "y": y, "direction": direction, "duration_ms": duration_ms},
        )

    def drag(self, from_target, to_target, phone_id: str | None = None) -> Job:
        """Drag from one point/element to another.

        Args:
            from_target: Either a point (unpacks to x, y) or a string selector.
            to_target: Either a point (unpacks to x, y) or a string selector.
            phone_id: Phone ID (optional).

        Note:
            When using selectors, both from_target and to_target must be strings.
        """
        pid = self._resolve_phone_id(phone_id)
        from_is_selector = isinstance(from_target, str)
        to_is_selector = isinstance(to_target, str)

        if from_is_selector or to_is_selector:
            if not (from_is_selector and to_is_selector):
                raise ValueError(
                    "For drag with selectors, both from_target and to_target must be strings"
                )
            return self._action_request(
                "POST",
                f"/phones/{pid}/drag/select",
                json={"from_selector": from_target, "to_selector": to_target},
            )
        from_x, from_y = from_target
        to_x, to_y = to_target
        return self._action_request(
            "POST",
            f"/phones/{pid}/drag",
            json={"from_x": from_x, "from_y": from_y, "to_x": to_x, "to_y": to_y},
        )

    def hold_and_drag(
        self,
        from_point,
        to_point,
        hold_duration_ms: int = 500,
        phone_id: str | None = None,
    ) -> Job:
        """Hold and drag gesture."""
        pid = self._resolve_phone_id(phone_id)
        from_x, from_y = from_point
        to_x, to_y = to_point
        return self._action_request(
            "POST",
            f"/phones/{pid}/hold-and-drag",
            json={
                "from_x": from_x,
                "from_y": from_y,
                "to_x": to_x,
                "to_y": to_y,
                "hold_duration_ms": hold_duration_ms,
            },
        )

    def pinch(
        self,
        target,
        action: Literal["pinch_in", "pinch_out", "rotate_cw", "rotate_ccw"],
        phone_id: str | None = None,
    ) -> Job:
        """Pinch gesture at a point or described element.

        Args:
            target: Either a point (unpacks to x, y) or a string selector.
            action: Type of pinch action.
            phone_id: Phone ID (optional).
        """
        pid = self._resolve_phone_id(phone_id)
        if isinstance(target, str):
            return self._action_request(
                "POST",
                f"/phones/{pid}/pinch/select",
                json={"selector": target, "action": action},
            )
        x, y = target
        return self._action_request(
            "POST",
            f"/phones/{pid}/pinch",
            json={"x": x, "y": y, "action": action},
        )

    # === Device Actions ===

    def home(self, phone_id: str | None = None) -> Job:
        """Press home button."""
        pid = self._resolve_phone_id(phone_id)
        return self._action_request("POST", f"/phones/{pid}/home")

    def app_switcher(self, phone_id: str | None = None) -> Job:
        """Open app switcher."""
        pid = self._resolve_phone_id(phone_id)
        return self._action_request("POST", f"/phones/{pid}/app-switcher")

    def control_center(self, phone_id: str | None = None) -> Job:
        """Open control center."""
        pid = self._resolve_phone_id(phone_id)
        return self._action_request("POST", f"/phones/{pid}/control-center")

    def lock(self, phone_id: str | None = None) -> Job:
        """Lock the device."""
        pid = self._resolve_phone_id(phone_id)
        return self._action_request("POST", f"/phones/{pid}/lock")

    def rotate(
        self,
        orientation: Literal["portrait", "left", "right", "upside_down"] = "portrait",
        phone_id: str | None = None,
    ) -> Job:
        """Rotate device."""
        pid = self._resolve_phone_id(phone_id)
        return self._action_request(
            "POST", f"/phones/{pid}/rotate", json={"orientation": orientation}
        )

    def volume_up(self, phone_id: str | None = None) -> Job:
        """Volume up."""
        pid = self._resolve_phone_id(phone_id)
        return self._action_request("POST", f"/phones/{pid}/volume-up")

    def volume_down(self, phone_id: str | None = None) -> Job:
        """Volume down."""
        pid = self._resolve_phone_id(phone_id)
        return self._action_request("POST", f"/phones/{pid}/volume-down")

    def action_button(self, phone_id: str | None = None) -> Job:
        """Press action button."""
        pid = self._resolve_phone_id(phone_id)
        return self._action_request("POST", f"/phones/{pid}/action-button")

    def spotlight(self, phone_id: str | None = None) -> Job:
        """Open spotlight."""
        pid = self._resolve_phone_id(phone_id)
        return self._action_request("POST", f"/phones/{pid}/spotlight")

    def siri(self, phone_id: str | None = None) -> Job:
        """Activate Siri."""
        pid = self._resolve_phone_id(phone_id)
        return self._action_request("POST", f"/phones/{pid}/siri")

    # === Convenience Actions ===

    def unlock(self, passcode: str | None = None, phone_id: str | None = None) -> Job:
        """Unlock the device."""
        pid = self._resolve_phone_id(phone_id)
        json_data = {}
        if passcode:
            json_data["passcode"] = passcode
        return self._action_request("POST", f"/phones/{pid}/unlock", json=json_data)

    def open_app(self, app_name: str, phone_id: str | None = None) -> Job:
        """Open an app by name."""
        pid = self._resolve_phone_id(phone_id)
        return self._action_request(
            "POST", f"/phones/{pid}/open-app", json={"app_name": app_name}
        )

    def type_text(
        self,
        text: str,
        method: Literal["keys", "paste"] = "keys",
        phone_id: str | None = None,
    ) -> Job:
        """Type text."""
        pid = self._resolve_phone_id(phone_id)
        return self._action_request(
            "POST", f"/phones/{pid}/type", json={"text": text, "method": method}
        )

    def run_shortcut(
        self,
        index: int | None = None,
        name: str | None = None,
        phone_id: str | None = None,
    ) -> Job:
        """Run a shortcut by index or name."""
        pid = self._resolve_phone_id(phone_id)
        json_data = {}
        if index is not None:
            json_data["index"] = index
        if name is not None:
            json_data["name"] = name
        return self._action_request("POST", f"/phones/{pid}/shortcut", json=json_data)

    # === Mac Control ===

    def enable_switch_control(self, mac_id: str) -> Job:
        """Enable Switch Control on a Mac."""
        return self._action_request("POST", f"/macs/{mac_id}/enable-switch-control")

    def disable_switch_control(self, mac_id: str) -> Job:
        """Disable Switch Control on a Mac."""
        return self._action_request("POST", f"/macs/{mac_id}/disable-switch-control")
