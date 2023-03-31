from ecs import component
import pygame as pg


@component
class Position:
    x: int
    y: int

@component
class Velocity:
    x: int
    y: int


@component
class AI:
    pass


@component
class Renderable:
    sprite: pg.Surface

@component
class Animation:
    sheet: list[pg.Surface]
    frame_dt: int
    curr: int = 0
    elapsed: int = 0
    once: bool = False


@component
class Player:
    pass