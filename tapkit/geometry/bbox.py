"""BBox and NormalizedBBox bounding box primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .point import Point, NormalizedPoint


@dataclass(frozen=True, slots=True)
class BBox:
    """Absolute bounding box in pixel coordinates."""

    x1: int
    y1: int
    x2: int
    y2: int

    def __iter__(self):
        """Allow tuple unpacking: x1, y1, x2, y2 = bbox"""
        return iter((self.x1, self.y1, self.x2, self.y2))

    def __getitem__(self, index: int):
        """Allow index access: bbox[0], bbox[1], etc."""
        return (self.x1, self.y1, self.x2, self.y2)[index]

    @property
    def width(self) -> int:
        """Width of the bounding box."""
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        """Height of the bounding box."""
        return self.y2 - self.y1

    @property
    def center(self) -> Point:
        """Center point of the bounding box."""
        return Point(x=(self.x1 + self.x2) // 2, y=(self.y1 + self.y2) // 2)

    def as_tuple(self) -> Tuple[int, int, int, int]:
        """Return coordinates as a tuple (x1, y1, x2, y2)."""
        return (self.x1, self.y1, self.x2, self.y2)

    def contains(self, point: Point) -> bool:
        """Check if a point is inside the bounding box."""
        return self.x1 <= point.x <= self.x2 and self.y1 <= point.y <= self.y2

    @classmethod
    def from_center(cls, center: Point, width: int, height: int) -> BBox:
        """Create a bounding box centered on a point."""
        half_w = width // 2
        half_h = height // 2
        return cls(
            x1=center.x - half_w,
            y1=center.y - half_h,
            x2=center.x + half_w,
            y2=center.y + half_h,
        )


@dataclass(frozen=True, slots=True)
class NormalizedBBox:
    """Bounding box with coordinates normalized to 0.0-1.0."""

    x1: float
    y1: float
    x2: float
    y2: float

    def __iter__(self):
        """Allow tuple unpacking: x1, y1, x2, y2 = bbox"""
        return iter((self.x1, self.y1, self.x2, self.y2))

    def __getitem__(self, index: int):
        """Allow index access: bbox[0], bbox[1], etc."""
        return (self.x1, self.y1, self.x2, self.y2)[index]

    @property
    def center(self) -> NormalizedPoint:
        """Center point of the bounding box."""
        return NormalizedPoint(x=(self.x1 + self.x2) / 2, y=(self.y1 + self.y2) / 2)

    def as_tuple(self) -> Tuple[float, float, float, float]:
        """Return coordinates as a tuple (x1, y1, x2, y2)."""
        return (self.x1, self.y1, self.x2, self.y2)

    def to_absolute(self, width: int, height: int) -> BBox:
        """Convert to absolute pixel coordinates given screen dimensions."""
        return BBox(
            x1=int(self.x1 * width),
            y1=int(self.y1 * height),
            x2=int(self.x2 * width),
            y2=int(self.y2 * height),
        )

    @classmethod
    def from_1000_scale(
        cls, x1: float, y1: float, x2: float, y2: float
    ) -> NormalizedBBox:
        """Convert from 0-1000 range (used by some agent models)."""
        return cls(x1=x1 / 1000, y1=y1 / 1000, x2=x2 / 1000, y2=y2 / 1000)

    @classmethod
    def from_absolute(cls, bbox: BBox, width: int, height: int) -> NormalizedBBox:
        """Convert from absolute pixel coordinates."""
        return cls(
            x1=bbox.x1 / width,
            y1=bbox.y1 / height,
            x2=bbox.x2 / width,
            y2=bbox.y2 / height,
        )
