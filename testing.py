import ecs
import systems
from components import Position, Renderable, Velocity


world = ecs.World()
player = world.add_entity(Position(50, 3), Renderable("o"), Velocity(0, 0))

render = systems.RenderSystem()
ctrl = systems.InputSystem()
move = systems.MovementSystem()
render.update(world)
ctrl.update(world, player, "left")
render.update(world)

while True:
    direction = input("Direction: ")
    if direction == "q":
        break
    ctrl.update(world, player, direction)
    move.update(world)
    render.update(world)