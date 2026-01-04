"""TapKit Python SDK.

Control iPhones programmatically via the TapKit API.

Quick Start:
    from tapkit import TapKitClient

    client = TapKitClient()
    phone = client.get_phone()

    # Tap center of screen
    phone.tap(phone.screen.center)

    # Take screenshot
    screenshot = phone.screenshot()

With geometry utilities:
    from tapkit import TapKitClient
    from tapkit.geometry import Point, BBox

    phone.tap(Point(100, 200))
    phone.tap(bbox.center)
"""

from .client import TapKitClient
from .exceptions import TapKitError
from .models import Job, JobStatus, Status
from .phone import Phone

__all__ = [
    "TapKitClient",
    "TapKitError",
    "Job",
    "JobStatus",
    "Phone",
    "Status",
]
