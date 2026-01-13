# TapKit Python SDK

Python SDK for controlling iPhones programmatically via the TapKit API.

## Installation

```bash
pip install tapkit
```

Or install from source:

```bash
pip install git+https://github.com/Jootsing-Research/tapkit-python.git
```

## Requirements

- Python 3.11 or later
- A TapKit account with API key
- TapKit Mac companion app running
- An iPhone connected through the Mac app

## Quick Start

### Authentication

Set your API key as an environment variable:

```bash
export TAPKIT_API_KEY="your-api-key"
```

Or pass it directly to the client:

```python
from tapkit import TapKitClient

client = TapKitClient(api_key="your-api-key")
```

### Basic Usage

```python
from tapkit import TapKitClient

# Initialize client
client = TapKitClient()

# Get your phone (works when you have exactly one phone)
phone = client.get_phone()

print(f"Connected to {phone.name}")
print(f"Screen size: {phone.width}x{phone.height}")

# Tap center of screen
phone.tap(phone.screen.center)

# Take a screenshot
screenshot = phone.screenshot()
with open("screen.png", "wb") as f:
    f.write(screenshot)
```

### Multiple Phones

```python
# List all phones
phones = client.list_phones()

# Get a specific phone by name
phone = client.phone("iPhone 15 Pro")

# Or set a default phone for the session
client.use_phone("iPhone 15 Pro")
client.tap((100, 200))  # Uses the default phone
```

## Features

### Gestures

```python
# Tap at coordinates
phone.tap((100, 200))

# Tap at screen center
phone.tap(phone.screen.center)

# Tap by description (uses vision AI)
phone.tap("the Settings icon")

# Double tap
phone.double_tap((100, 200))

# Tap and hold (long press)
phone.tap_and_hold((100, 200), duration_ms=1000)

# Flick (quick swipe)
phone.flick(phone.screen.center, "up")

# Pan (slower scroll)
phone.pan(phone.screen.center, "down", duration_ms=500)

# Drag from one point to another
phone.drag((100, 200), (300, 400))

# Hold and drag
phone.hold_and_drag((100, 200), (300, 400), hold_duration_ms=500)

# Pinch gestures
phone.pinch(phone.screen.center, "pinch_in")   # Zoom out
phone.pinch(phone.screen.center, "pinch_out")  # Zoom in
phone.pinch(phone.screen.center, "rotate_cw")  # Rotate clockwise
```

### Device Control

```python
# Navigation
phone.home()           # Go to home screen
phone.app_switcher()   # Open app switcher
phone.control_center() # Open control center
phone.spotlight()      # Open spotlight search
phone.siri()           # Activate Siri

# Lock/Unlock
phone.lock()
phone.unlock(passcode="123456")

# Volume
phone.volume_up()
phone.volume_down()

# Rotation
phone.rotate("portrait")
phone.rotate("left")
phone.rotate("right")

# Action button (iPhone 15 Pro+)
phone.action_button()
```

### App Control

```python
# Open an app
phone.open_app("Safari")

# Type text
phone.type_text("Hello, world!")
phone.type_text("pasted text", method="paste")  # Use clipboard

# Run iOS Shortcuts
phone.run_shortcut(name="My Shortcut")
phone.run_shortcut(index=0)  # Run first shortcut
```

### Screenshots

```python
# Capture screenshot as PNG bytes
screenshot = phone.screenshot()

# Save to file
with open("screenshot.png", "wb") as f:
    f.write(screenshot)
```

## Geometry Utilities

TapKit includes geometry primitives for working with coordinates:

```python
from tapkit.geometry import Point, BBox, NormalizedPoint, NormalizedBBox, Screen

# Points
point = Point(100, 200)
x, y = point  # Tuple unpacking works

# Bounding boxes
bbox = BBox(x1=100, y1=200, x2=300, y2=400)
phone.tap(bbox.center)  # Tap center of bounding box

# Normalized coordinates (0.0-1.0)
normalized = NormalizedPoint(0.5, 0.5)  # Center of screen
absolute = normalized.to_absolute(phone.width, phone.height)

# Screen utilities
screen = phone.screen
screen.center        # Center point
screen.contains(p)   # Check if point is in bounds
screen.clamp(p)      # Clamp point to screen bounds
```

## OAGI Integration

TapKit includes handlers for [OAGI](https://github.com/anthropics/oagi) workflows:

```python
from tapkit import TapKitClient
from tapkit.oagi import TapKitAsyncActionHandler, TapKitAsyncImageProvider

client = TapKitClient()
phone = client.get_phone()

# Create handlers
action_handler = TapKitAsyncActionHandler(phone)
image_provider = TapKitAsyncImageProvider(phone)

# Use with OAGI agents
# action_handler can execute OAGI Action objects
# image_provider provides screenshots for vision models
```

## Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `TAPKIT_API_KEY` | API key for authentication | Required |
| `TAPKIT_BASE_URL` | Base URL for API | `https://api.tapkit.ai/v1` |

## Documentation

For full documentation, visit [docs.tapkit.ai](https://docs.tapkit.ai).

## License

MIT
