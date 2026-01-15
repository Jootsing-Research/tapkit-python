import time

from oagi.types import Action, ActionType, parse_coords, parse_drag_coords, parse_scroll

from ..phone import Phone
from ..geometry import Screen, NormalizedPoint, Point


class TapKitActionHandler:
    """
    Handles actions to be executed using TapKit.

    This class provides functionality for handling and executing a sequence of
    actions using the TapKit library. It processes a list of actions and executes
    them as per the implementation.

    Methods:
        __call__: Executes the provided list of actions.

    Args:
        actions (list[Action]): List of actions to be processed and executed.
    """

    def __init__(self, phone: Phone):
        self._phone = phone
        self._screen = Screen(width=phone.width, height=phone.height)
        print("Init Sync Handler")

    def reset(self):
        print("Reset Sync")

    def _coords_from_1000_scale(self, x: float, y: float) -> Point:
        """Convert coordinates from 0-1000 range to absolute screen coordinates."""
        normalized = NormalizedPoint.from_1000_scale(x, y)
        absolute = self._screen.point_to_absolute(normalized)
        return self._screen.clamp(absolute)

    def _parse_coords(self, args_str: str) -> Point:
        """Extract x, y coordinates from argument string."""
        coords = parse_coords(args_str)
        if not coords:
            raise ValueError(f"Invalid coordinates format: {args_str}")
        return self._coords_from_1000_scale(coords[0], coords[1])

    def _parse_drag_coords(self, args_str: str) -> tuple[Point, Point]:
        """Extract start and end points from drag argument string."""
        coords = parse_drag_coords(args_str)
        if not coords:
            raise ValueError(f"Invalid drag coordinates format: {args_str}")
        start = self._coords_from_1000_scale(coords[0], coords[1])
        end = self._coords_from_1000_scale(coords[2], coords[3])
        return start, end

    def _parse_scroll(self, args_str: str) -> tuple[Point, str]:
        """Extract point and direction from scroll argument string."""
        result = parse_scroll(args_str)
        if not result:
            raise ValueError(f"Invalid scroll format: {args_str}")
        point = self._coords_from_1000_scale(result[0], result[1])
        return point, result[2]

    def _execute_single_action(self, action: Action) -> None:
        """Execute a single action once."""
        arg = action.argument.strip("()")  # Remove outer parentheses if present
        match action.type:
            case ActionType.CLICK:
                point = self._parse_coords(arg)
                self._phone.tap(point.as_tuple())

            case ActionType.LEFT_DOUBLE:
                point = self._parse_coords(arg)
                self._phone.double_tap(point.as_tuple())
            case ActionType.LEFT_TRIPLE:
                # We don't have a tripple tap at the moment
                point = self._parse_coords(arg)
                self._phone.double_tap(point.as_tuple())
            case ActionType.RIGHT_SINGLE:
                # Phones's don't have right clicks but I'm assuming the equivilant is a hold
                point = self._parse_coords(arg)
                self._phone.hold(point.as_tuple(), duration_ms=2000)
            case ActionType.DRAG:
                start, end = self._parse_drag_coords(arg)
                self._phone.drag(start.as_tuple(), end.as_tuple())
            case ActionType.HOTKEY:
                # Hotkeys aren't a thing for us, we need to capture all of the possible hotkeys and figure out what their mappings are
                pass
            case ActionType.TYPE:
                text = arg.strip("\"'")
                self._phone.type_text(text=text, method='keys')
            case ActionType.SCROLL:
                # TODO We should probably have multiple ways to scroll and make that configurable idk
                point, direction = self._parse_scroll(arg)
                if direction == 'down':
                    direction = 'up'
                elif direction == 'up':
                    direction = 'down'
                self._phone.flick(point.as_tuple(), direction)

            case ActionType.FINISH:
                self.reset()

            case ActionType.WAIT:
                # Wait for a short period
                # TODO introduce the wait timer
                time.sleep(3.0)
            case ActionType.CALL_USER:
                # TODO - integrate with out own kind of user human in the loop ideas
                print("User intervention requested")
            case _:
                # TODO - what do we do here? idk
                print(f"Unknown action type: {action.type}")

    def _execute_action(self, action: Action) -> None:
        """Execute an action, potentially multiple times."""
        count = action.count or 1

        for _ in range(count):
            self._execute_single_action(action)

    def __call__(self, actions: list[Action]) -> None:
        """Execute the provided list of actions."""
        for action in actions:
            try:
                self._execute_action(action)
            except Exception as e:
                print(f"Error executing action {action.type}: {e}")
                raise
