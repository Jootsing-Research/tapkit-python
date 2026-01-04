import asyncio

from oagi.types import Action

from ..phone import Phone
from .sync_action_handler import TapKitActionHandler


class TapKitAsyncActionHandler:
    """
    Async wrapper for TapKitActionHandler that runs actions in a thread pool.

    This allows TapKit operations to be non-blocking in async contexts,
    enabling concurrent execution of other async tasks while GUI actions are performed.
    """

    def __init__(self, phone: Phone):
        """Initialize with a phone object.

        Args:
            phone: TapKit phone object with id, width, and height properties
        """
        self.sync_handler = TapKitActionHandler(phone=phone)

    def reset(self):
        """Reset handler state.

        Delegates to the underlying synchronous handler's reset method.
        Called at automation start/end and when FINISH action is received.
        """
        self.sync_handler.reset()

    async def __call__(self, actions: list[Action]) -> None:
        """
        Execute actions asynchronously using a thread pool executor.

        This prevents PyAutoGUI operations from blocking the async event loop,
        allowing other coroutines to run while GUI actions are being performed.

        Args:
            actions: List of actions to execute
        """
        loop = asyncio.get_event_loop()
        # Run the synchronous handler in a thread pool to avoid blocking
        await loop.run_in_executor(None, self.sync_handler, actions)
