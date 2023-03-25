from ecs import component

@component
class Position:
    x: int
    y: int

@component
class Velocity:
    x: int
    y: int


@component
class Renderable:
    texture: str

