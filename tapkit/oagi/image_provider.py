import io

from PIL.Image import open as open_pil_image
from oagi import PILImage, ImageConfig

from ..phone import Phone


class TapKitAsyncImageProvider:
    """Async image provider that uses TapKit phone directly."""

    def __init__(self, phone: Phone):
        self._phone = phone
        self._last_screenshot = None

    async def __call__(self):
        screenshot_bytes = self._phone.screenshot()
        pil_image = open_pil_image(io.BytesIO(screenshot_bytes))
        screenshot = PILImage(image=pil_image)
        self._last_screenshot = screenshot.transform(config=ImageConfig())
        return self._last_screenshot

    async def last_image(self):
        if self._last_screenshot is None:
            return await self()
        return self._last_screenshot
