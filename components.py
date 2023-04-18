"""
Author: Victor Hernadi
Last edited: 2023-04-18
"""

from ecs import component
import pygame as pg


@component
class Position:
    """
    Position component.
    Args:
    x: x-coordinate
    y: y-coordinate
    """
    x: int
    y: int

@component
class Velocity:
    """
    Velocity component.
    Args:
    x: x-velocity component
    y: y-velocity component
    """
    x: int
    y: int


@component
class AI:
    """
    AI component marker.
    """
    pass


@component
class Renderable:
    """
    Renderable component.
    Args:
    sprite: the sprite to be rendered
    """
    sprite: pg.Surface

@component
class Animation:
    """
    Animation component.
    Args:
    sheet: the sprite-sheet to be used for animation
    frame_dt: the delta time to pass between animation frames
    curr: the current sprite selected for animation
    elapsed: the elapsed time
    once: False if this should be removed after one complete animation, True otherwise
    """
    sheet: list[pg.Surface]
    frame_dt: int
    curr: int = 0
    elapsed: int = 0
    once: bool = False


@component
class Player:
    """
    Player component marker.
    """
    pass