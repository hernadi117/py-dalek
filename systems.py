from ecs import System
from components import Position, Velocity


class MovementSystem(System):

    def __init__(self) -> None:
        super().__init__()


    def update(self, *args, **kwargs) -> None:
        for _, (pos, vel) in self.world.get_component(Position, Velocity):
            pos.x, pos.y += vel.x, vel.y