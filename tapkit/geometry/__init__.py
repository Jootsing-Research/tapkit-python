"""Geometry primitives for coordinate handling."""

from .bbox import BBox, NormalizedBBox
from .point import NormalizedPoint, Point
from .screen import Screen

__all__ = [
    "Point",
    "NormalizedPoint",
    "BBox",
    "NormalizedBBox",
    "Screen",
]
