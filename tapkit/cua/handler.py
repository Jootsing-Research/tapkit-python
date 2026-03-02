"""CUA AsyncComputerHandler implementation for TapKit phones.

Handles screenshot scaling and coordinate conversion so that
vision models see a resolution they perform well at (max 1344px
longest edge by default), while all touch actions are mapped
back to actual phone pixel coordinates.
"""

from __future__ import annotations

import asyncio
import base64
import io
from typing import Dict, List, Literal, Optional, Union

from PIL import Image

from agent.computers import AsyncComputerHandler

from ..phone import Phone

DEFAULT_MAX_LONG_EDGE = 1344


class TapKitComputerHandler(AsyncComputerHandler):
    """CUA-compatible handler that controls a TapKit phone.

    Implements CUA's AsyncComputerHandler interface so any model
    supported by ComputerAgent (Anthropic, OpenAI, UI-TARS, etc.)
    can drive a real iPhone through TapKit.

    Screenshots are scaled down so models see a resolution they
    were trained on. Coordinates from the model are scaled back
    up to actual phone pixels for all touch actions.

    Args:
        phone: A TapKit Phone instance.
        max_long_edge: Maximum pixels for the longest screen edge
            in the scaled-down image the model sees. Defaults to 1344.
    """

    def __init__(self, phone: Phone, max_long_edge: int = DEFAULT_MAX_LONG_EDGE):
        self._phone = phone

        # Actual phone dimensions
        self._actual_w = phone.width
        self._actual_h = phone.height

        # Scaling: shrink so longest edge <= max_long_edge
        longest = max(self._actual_w, self._actual_h)
        self._scale = min(1.0, max_long_edge / longest)
        self._scaled_w = int(self._actual_w * self._scale)
        self._scaled_h = int(self._actual_h * self._scale)

    def _to_actual(self, x: int, y: int) -> tuple[int, int]:
        """Scale coordinates from model space to actual phone pixels."""
        return int(x / self._scale), int(y / self._scale)

    # === CUA AsyncComputerHandler Interface ===

    async def get_environment(self) -> Literal["windows", "mac", "linux", "browser"]:
        return "mac"

    async def get_dimensions(self) -> tuple[int, int]:
        """Return scaled dimensions — this is what the model sees."""
        return (self._scaled_w, self._scaled_h)

    async def screenshot(self, text: Optional[str] = None) -> str:
        """Capture screenshot, resize to scaled dimensions, return as base64 PNG."""
        screenshot_bytes = self._phone.screenshot()
        pil_image = Image.open(io.BytesIO(screenshot_bytes))
        resized = pil_image.resize((self._scaled_w, self._scaled_h))

        buf = io.BytesIO()
        resized.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    async def click(self, x: int, y: int, button: str = "left") -> None:
        ax, ay = self._to_actual(x, y)
        if button == "right":
            self._phone.hold((ax, ay), duration_ms=1000)
        else:
            self._phone.tap((ax, ay))

    async def double_click(self, x: int, y: int) -> None:
        ax, ay = self._to_actual(x, y)
        self._phone.double_tap((ax, ay))

    async def scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        ax, ay = self._to_actual(x, y)
        # CUA scroll_y: negative = scroll up, positive = scroll down.
        # phone.flick direction is finger movement, so:
        #   scroll down (show content below) = flick up (finger moves up)
        if scroll_y < 0:
            self._phone.flick(target=(ax, ay), direction="down")
        elif scroll_y > 0:
            self._phone.flick(target=(ax, ay), direction="up")
        elif scroll_x < 0:
            self._phone.flick(target=(ax, ay), direction="right")
        elif scroll_x > 0:
            self._phone.flick(target=(ax, ay), direction="left")

    async def type(self, text: str) -> None:
        self._phone.type_text(text=text, method="shortcut")

    async def wait(self, ms: int = 1000) -> None:
        await asyncio.sleep(ms / 1000.0)

    async def move(self, x: int, y: int) -> None:
        pass  # No cursor on phone

    async def keypress(self, keys: Union[List[str], str]) -> None:
        if isinstance(keys, str):
            keys = [keys]

        key_combo = "+".join(keys).lower()

        if key_combo in ("escape", "back"):
            self._phone.escape()
        elif key_combo in ("home", "cmd+h", "super+h", "cmd+q"):
            self._phone.home()
        elif "tab" in key_combo and ("cmd" in key_combo or "alt" in key_combo):
            self._phone.app_switcher()
        elif key_combo in ("return", "enter"):
            pass  # Let the agent tap the on-screen button instead
        elif key_combo in ("backspace", "delete"):
            pass
        elif "+" in key_combo:
            pass  # Ignore unknown keyboard shortcuts
        else:
            # Single character keys — type them
            for key in keys:
                if len(key) == 1:
                    self._phone.type_text(text=key, method="shortcut")

    async def drag(self, path: List[Dict[str, int]]) -> None:
        if len(path) < 2:
            return
        start = path[0]
        end = path[-1]
        ax1, ay1 = self._to_actual(start.get("x", 0), start.get("y", 0))
        ax2, ay2 = self._to_actual(end.get("x", 0), end.get("y", 0))
        self._phone.drag(from_target=(ax1, ay1), to_target=(ax2, ay2))

    async def get_current_url(self) -> str:
        return ""

    async def left_mouse_down(self, x: Optional[int] = None, y: Optional[int] = None) -> None:
        pass  # Phone touches are atomic

    async def left_mouse_up(self, x: Optional[int] = None, y: Optional[int] = None) -> None:
        pass
