"""Point and NormalizedPoint coordinate primitives."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True, slots=True)
class Point:
    """Absolute pixel coordinates on a screen."""

    x: int
    y: int

    def __iter__(self):
        """Allow tuple unpacking: x, y = point"""
        return iter((self.x, self.y))

    def __getitem__(self, index: int):
        """Allow index access: point[0], point[1]"""
        return (self.x, self.y)[index]

    def as_tuple(self) -> Tuple[int, int]:
        """Return coordinates as a tuple (x, y)."""
        return (self.x, self.y)

    def distance_to(self, other: Point) -> float:
        """Calculate Euclidean distance to another point."""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


@dataclass(frozen=True, slots=True)
class NormalizedPoint:
    """Coordinates normalized to 0.0-1.0 range relative to a screen/image."""

    x: float
    y: float

    def __iter__(self):
        """Allow tuple unpacking: x, y = point"""
        return iter((self.x, self.y))

    def __getitem__(self, index: int):
        """Allow index access: point[0], point[1]"""
        return (self.x, self.y)[index]

    def as_tuple(self) -> Tuple[float, float]:
        """Return coordinates as a tuple (x, y)."""
        return (self.x, self.y)

    def to_absolute(self, width: int, height: int) -> Point:
        """Convert to absolute pixel coordinates given screen dimensions."""
        return Point(x=int(self.x * width), y=int(self.y * height))

    @classmethod
    def from_1000_scale(cls, x: float, y: float) -> NormalizedPoint:
        """Convert from 0-1000 range (used by some agent models)."""
        return cls(x=x / 1000.0, y=y / 1000.0)

    @classmethod
    def from_100_scale(cls, x: float, y: float) -> NormalizedPoint:
        """Convert from 0-100 percentage range."""
        return cls(x=x / 100.0, y=y / 100.0)

    @classmethod
    def from_absolute(cls, point: Point, width: int, height: int) -> NormalizedPoint:
        """Convert from absolute pixel coordinates."""
        return cls(x=point.x / width, y=point.y / height)
