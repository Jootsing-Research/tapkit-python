"""CUA (Computer Use Agent) integration for TapKit.

Provides an AsyncComputerHandler that lets CUA's ComputerAgent
control a TapKit phone with any supported model.

Usage:
    from tapkit import TapKitClient
    from tapkit.cua import TapKitComputerHandler
    from agent import ComputerAgent

    phone = TapKitClient().phone("my-phone-id")
    handler = TapKitComputerHandler(phone)

    agent = ComputerAgent(
        model="openai/computer-use-preview",
        tools=[handler],
    )

    async for result in agent.run([{"role": "user", "content": "Open Settings"}]):
        print(result)
"""

from .handler import TapKitComputerHandler

__all__ = [
    "TapKitComputerHandler",
]
