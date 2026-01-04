"""Screen dimensions and coordinate conversion utilities."""

from __future__ import annotations

from dataclasses import dataclass

from .bbox import BBox, NormalizedBBox
from .point import NormalizedPoint, Point


@dataclass(frozen=True, slots=True)
class Screen:
    """Represents screen dimensions and provides coordinate conversions."""

    width: int
    height: int

    @property
    def center(self) -> Point:
        """Center point of the screen."""
        return Point(x=self.width // 2, y=self.height // 2)

    def contains(self, point: Point) -> bool:
        """Check if a point is within screen bounds."""
        return 0 <= point.x < self.width and 0 <= point.y < self.height

    def clamp(self, point: Point) -> Point:
        """Clamp a point to be within screen bounds."""
        return Point(
            x=max(0, min(point.x, self.width - 1)),
            y=max(0, min(point.y, self.height - 1)),
        )

    def point_to_normalized(self, point: Point) -> NormalizedPoint:
        """Convert an absolute point to normalized coordinates."""
        return NormalizedPoint.from_absolute(point, self.width, self.height)

    def point_to_absolute(self, point: NormalizedPoint) -> Point:
        """Convert a normalized point to absolute coordinates."""
        return point.to_absolute(self.width, self.height)

    def bbox_to_normalized(self, bbox: BBox) -> NormalizedBBox:
        """Convert an absolute bounding box to normalized coordinates."""
        return NormalizedBBox.from_absolute(bbox, self.width, self.height)

    def bbox_to_absolute(self, bbox: NormalizedBBox) -> BBox:
        """Convert a normalized bounding box to absolute coordinates."""
        return bbox.to_absolute(self.width, self.height)
