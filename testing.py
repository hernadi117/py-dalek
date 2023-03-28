import ecs
import systems
from components import Position, Renderable, Velocity
import pygame as pg
from utils import load_map
from tiles import get_tile_map, get_animated_tile_components


#world = ecs.World()
#player = world.add_entity(Position(50, 3), Renderable("o"), Velocity(0, 0))

#render = systems.RenderSystem()
#ctrl = systems.InputSystem()
#move = systems.MovementSystem()
#render.update(world)
#ctrl.update(world, player, "left")
#render.update(world)

#while True:
#    direction = input("Direction: ")
#    if direction == "q":
#        break
#    ctrl.update(world, player, direction)
#    move.update(world)
#    render.update(world)






def main():

    type_map = load_map("map.txt")

    pg.init()
    window = pg.display.set_mode((len(type_map[0]) * 16 * 3, len(type_map) * 16 * 3), pg.DOUBLEBUF)
    pg.display.set_caption("Best Game")
    clock = pg.time.Clock()
    world = ecs.World()
    player = world.add_entity(Position(4, 3), Renderable(pg.Rect(0, 0, 0, 0)), Velocity(0, 0))
    ctrl = systems.InputSystem()
    render = systems.RenderSystem(window, get_tile_map(type_map))
    animation = systems.AnimationSystem()

    for comps in get_animated_tile_components(type_map):
        print(comps)
        world.add_entity(*comps)

    

    world.add_system([animation, render])

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                break
        world.update(clock)
        clock.tick(60)


if __name__ == "__main__":
    main()