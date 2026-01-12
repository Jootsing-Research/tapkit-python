"""Phone class for device control."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from .geometry import Screen
from .models import Job

if TYPE_CHECKING:
    from .client import TapKitClient


class Phone:
    """A phone you can control.

    The Phone class is the primary way to interact with devices. It holds
    identity, dimensions, and all action methods.

    Examples:
        phone = client.get_phone()
        phone.tap(phone.screen.center)
        phone.tap((100, 200))

        # With bounding boxes from vision models
        button = BBox(x1=100, y1=200, x2=300, y2=250)
        phone.tap(button.center)
    """

    def __init__(
        self,
        id: str,
        name: str,
        unique_id: str,
        width: int,
        height: int,
        client: "TapKitClient",
    ):
        """Initialize a Phone instance.

        Args:
            id: Server-assigned phone ID.
            name: Device name (e.g., "iPhone 15").
            unique_id: Hardware identifier.
            width: Screen width in pixels.
            height: Screen height in pixels.
            client: TapKitClient instance for making requests.
        """
        self.id = id
        self.name = name
        self.unique_id = unique_id
        self.width = width
        self.height = height
        self._client = client

    @property
    def screen(self) -> Screen:
        """Get a Screen object for coordinate utilities."""
        return Screen(width=self.width, height=self.height)

    def __repr__(self) -> str:
        return f"Phone(id={self.id!r}, name={self.name!r}, width={self.width}, height={self.height})"

    # === Gesture Actions ===

    def tap(self, target) -> Job:
        """Tap at a point or described element.

        Args:
            target: Either:
                - A point that unpacks to (x, y) - tuple, list, Point, bbox.center, etc.
                - A string description of what to tap (e.g., "the blue button")

        Examples:
            phone.tap((100, 200))
            phone.tap(phone.screen.center)
            phone.tap(bbox.center)
            phone.tap("the Settings icon")
            phone.tap("the blue Submit button")
        """
        if isinstance(target, str):
            # Use vision AI to find and tap the described element
            return self._client._action_request(
                "POST", f"/phones/{self.id}/tap/select", json={"selector": target}
            )
        else:
            # Tap at coordinates
            x, y = target
            return self._client._action_request(
                "POST", f"/phones/{self.id}/tap", json={"x": x, "y": y}
            )

    def tap_with_delays(self, x_delay: float, y_delay: float) -> Job:
        """Tap using raw scan delay times instead of coordinates.

        Args:
            x_delay: X-axis scan delay time.
            y_delay: Y-axis scan delay time.
        """
        return self._client._action_request(
            "POST",
            f"/phones/{self.id}/tap-with-delays",
            json={"x_delay": x_delay, "y_delay": y_delay},
        )

    def double_tap(self, target) -> Job:
        """Double tap at a point or described element.

        Args:
            target: Either:
                - A point that unpacks to (x, y) - tuple, list, Point, bbox.center, etc.
                - A string description of what to double tap (e.g., "the image thumbnail")

        Examples:
            phone.double_tap((100, 200))
            phone.double_tap("the photo to zoom in")
        """
        if isinstance(target, str):
            return self._client._action_request(
                "POST", f"/phones/{self.id}/double-tap/select", json={"selector": target}
            )
        x, y = target
        return self._client._action_request(
            "POST", f"/phones/{self.id}/double-tap", json={"x": x, "y": y}
        )

    def hold(self, target, duration_ms: int = 1000) -> Job:
        """Hold (long press) at a point or described element.

        Args:
            target: Either:
                - A point that unpacks to (x, y) - tuple, list, Point, bbox.center, etc.
                - A string description of what to hold (e.g., "the app icon")
            duration_ms: Hold duration in milliseconds.

        Examples:
            phone.hold((100, 200), duration_ms=2000)
            phone.hold("the app icon to delete")
        """
        if isinstance(target, str):
            return self._client._action_request(
                "POST",
                f"/phones/{self.id}/tap-and-hold/select",
                json={"selector": target, "duration_ms": duration_ms},
            )
        x, y = target
        return self._client._action_request(
            "POST",
            f"/phones/{self.id}/tap-and-hold",
            json={"x": x, "y": y, "duration_ms": duration_ms},
        )

    def flick(self, target, direction: Literal["up", "down", "left", "right"]) -> Job:
        """Flick gesture (quick swipe) from a point or described element.

        Args:
            target: Either:
                - A point that unpacks to (x, y) - tuple, list, Point, bbox.center, etc.
                - A string description of where to flick from (e.g., "the scrollable list")
            direction: Flick direction.

        Examples:
            phone.flick((100, 200), "up")
            phone.flick("the message list", "down")
        """
        if isinstance(target, str):
            return self._client._action_request(
                "POST",
                f"/phones/{self.id}/flick/select",
                json={"selector": target, "direction": direction},
            )
        x, y = target
        return self._client._action_request(
            "POST",
            f"/phones/{self.id}/flick",
            json={"x": x, "y": y, "direction": direction},
        )

    def pan(
        self,
        point,
        direction: Literal["up", "down", "left", "right"],
        duration_ms: int = 500,
    ) -> Job:
        """Pan gesture (slower scroll).

        Args:
            point: Anything that unpacks to (x, y).
            direction: Pan direction.
            duration_ms: Pan duration in milliseconds.
        """
        x, y = point
        return self._client._action_request(
            "POST",
            f"/phones/{self.id}/pan",
            json={"x": x, "y": y, "direction": direction, "duration_ms": duration_ms},
        )

    def drag(self, from_target, to_target) -> Job:
        """Drag from one point/element to another.

        Args:
            from_target: Either:
                - A point that unpacks to (x, y)
                - A string description of where to drag from
            to_target: Either:
                - A point that unpacks to (x, y)
                - A string description of where to drag to

        Note:
            When using selectors, both from_target and to_target must be strings.
            Mixed coordinate/selector usage is not supported.

        Examples:
            phone.drag((100, 200), (300, 400))
            phone.drag("the slider handle", "the right end of the slider")
        """
        from_is_selector = isinstance(from_target, str)
        to_is_selector = isinstance(to_target, str)

        if from_is_selector or to_is_selector:
            if not (from_is_selector and to_is_selector):
                raise ValueError(
                    "For drag with selectors, both from_target and to_target must be strings"
                )
            return self._client._action_request(
                "POST",
                f"/phones/{self.id}/drag/select",
                json={"from_selector": from_target, "to_selector": to_target},
            )
        from_x, from_y = from_target
        to_x, to_y = to_target
        return self._client._action_request(
            "POST",
            f"/phones/{self.id}/drag",
            json={"from_x": from_x, "from_y": from_y, "to_x": to_x, "to_y": to_y},
        )

    def hold_and_drag(
        self, from_point, to_point, hold_duration_ms: int = 500
    ) -> Job:
        """Hold at a point, then drag to another point.

        Args:
            from_point: Starting point (unpacks to x, y).
            to_point: Ending point (unpacks to x, y).
            hold_duration_ms: Duration to hold before dragging.
        """
        from_x, from_y = from_point
        to_x, to_y = to_point
        return self._client._action_request(
            "POST",
            f"/phones/{self.id}/hold-and-drag",
            json={
                "from_x": from_x,
                "from_y": from_y,
                "to_x": to_x,
                "to_y": to_y,
                "hold_duration_ms": hold_duration_ms,
            },
        )

    def pinch(
        self, target, action: Literal["pinch_in", "pinch_out", "rotate_cw", "rotate_ccw"]
    ) -> Job:
        """Pinch/zoom/rotate gesture at a point or described element.

        Args:
            target: Either:
                - A point that unpacks to (x, y) - tuple, list, Point, bbox.center, etc.
                - A string description of where to pinch (e.g., "the image")
            action: Type of pinch action.

        Examples:
            phone.pinch((100, 200), "pinch_out")
            phone.pinch("the map", "pinch_in")
        """
        if isinstance(target, str):
            return self._client._action_request(
                "POST",
                f"/phones/{self.id}/pinch/select",
                json={"selector": target, "action": action},
            )
        x, y = target
        return self._client._action_request(
            "POST",
            f"/phones/{self.id}/pinch",
            json={"x": x, "y": y, "action": action},
        )

    # === Device Actions ===

    def home(self) -> Job:
        """Press home button / go to home screen."""
        return self._client._action_request("POST", f"/phones/{self.id}/home")

    def app_switcher(self) -> Job:
        """Open the app switcher."""
        return self._client._action_request("POST", f"/phones/{self.id}/app-switcher")

    def control_center(self) -> Job:
        """Open control center."""
        return self._client._action_request("POST", f"/phones/{self.id}/control-center")

    def lock(self) -> Job:
        """Lock the device screen."""
        return self._client._action_request("POST", f"/phones/{self.id}/lock")

    def rotate(
        self, orientation: Literal["portrait", "left", "right", "upside_down"]
    ) -> Job:
        """Rotate device orientation.

        Args:
            orientation: Target orientation.
        """
        return self._client._action_request(
            "POST", f"/phones/{self.id}/rotate", json={"orientation": orientation}
        )

    def volume_up(self) -> Job:
        """Increase volume."""
        return self._client._action_request("POST", f"/phones/{self.id}/volume-up")

    def volume_down(self) -> Job:
        """Decrease volume."""
        return self._client._action_request("POST", f"/phones/{self.id}/volume-down")

    def action_button(self) -> Job:
        """Press the action button (iPhone 15 Pro+)."""
        return self._client._action_request("POST", f"/phones/{self.id}/action-button")

    def spotlight(self) -> Job:
        """Open Spotlight search."""
        return self._client._action_request("POST", f"/phones/{self.id}/spotlight")

    def siri(self) -> Job:
        """Activate Siri."""
        return self._client._action_request("POST", f"/phones/{self.id}/siri")

    # === Convenience Actions ===

    def unlock(self, passcode: str | None = None) -> Job:
        """Unlock the device.

        Args:
            passcode: Optional passcode to enter.
        """
        json_data = {}
        if passcode:
            json_data["passcode"] = passcode
        return self._client._action_request(
            "POST", f"/phones/{self.id}/unlock", json=json_data
        )

    def open_app(self, app_name: str) -> Job:
        """Open an app by name.

        Args:
            app_name: Name of the app to open.
        """
        return self._client._action_request(
            "POST", f"/phones/{self.id}/open-app", json={"app_name": app_name}
        )

    def type_text(self, text: str, method: Literal["keys", "shortcut"] = "keys") -> Job:
        """Type text.

        Args:
            text: Text to type.
            method: Input method:
                - "keys": Keystroke simulation via keyboard extension
                - "shortcut": iOS Shortcut copies text to clipboard, then vision-guided paste
        """
        return self._client._action_request(
            "POST", f"/phones/{self.id}/type", json={"text": text, "method": method}
        )

    def run_shortcut(self, index: int | None = None, name: str | None = None) -> Job:
        """Run an iOS Shortcut.

        Args:
            index: Shortcut index (0-based).
            name: Shortcut name.
        """
        json_data = {}
        if index is not None:
            json_data["index"] = index
        if name is not None:
            json_data["name"] = name
        return self._client._action_request(
            "POST", f"/phones/{self.id}/shortcut", json=json_data
        )

    # === Screenshots ===

    def screenshot(self) -> bytes:
        """Capture and return a screenshot as PNG bytes.

        Returns:
            PNG image data as bytes.
        """
        resp = self._client._request("GET", f"/phones/{self.id}/screenshot")
        return resp.content
