from ecs import System, subscribe, publish, World
from components import Position, Velocity, Renderable
import os

class MovementSystem(System):

    def __init__(self) -> None:
        super().__init__()


    def update(self, world: World) -> None:
        for _, (pos, vel) in world.get_component(Position, Velocity):
            print(pos, vel)
            pos.x += vel.x
            pos.y += vel.y


class RenderSystem(System):

    def __init__(self) -> None:
        super().__init__()

    
    def create_map(self, width, height):
        return [["." for _ in range(width)] for _ in range(height)]

    def update(self, world: World) -> None:
        game_map = self.create_map(100, 20)
        for _, (pos, render) in world.get_component(Position, Renderable):
            game_map[pos.y][pos.x] = render.texture

        os.system('cls' if os.name == 'nt' else 'clear')
        buffer = "\n".join(str("".join(i for i in y)) for y in game_map)
        print(buffer)


class InputSystem(System):

    def __init__(self) -> None:
        super().__init__()

    
    def update(self, world: World, *args):
        entity_id, direction = args
        vel = world.component_for(entity_id, Velocity)[0]
        if direction == "up":
            vel.x = 0
            vel.y = -1
        if direction == "down":
            vel.x = 0
            vel.y = 1
        if direction == "left":
            vel.x = -1
            vel.y = 0
        if direction == "right":
            vel.x = 1
            vel.y = 0