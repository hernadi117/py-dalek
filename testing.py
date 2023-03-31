import ecs
import systems
from components import Position, Renderable, Velocity, Player
import pygame as pg
from utils import load_map
from tiles import get_tile_map, get_animated_tile_components, get_dalek_components
from itertools import chain


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
    sprite: pg.Surface = pg.Surface((48, 48)).convert()
    player = world.add_entity(Position(10, 1), Renderable(sprite), Velocity(0, 0), Player())
    ctrl = systems.InputSystem(player)
    movement = systems.MovementSystem()
    render = systems.RenderSystem(window, get_tile_map(type_map))
    animation = systems.AnimationSystem()
    ai_ctrl = systems.EnemyControl()

    wall_pos = set()
    for comps in get_animated_tile_components(type_map):
        world.add_entity(*comps)
        for comp in comps:
            if isinstance(comp, Position):
                wall_pos.add((comp.x, comp.y))
    
    for comps in get_dalek_components(type_map):
        world.add_entity(*comps)
    
    
    collision = systems.CollisionSystem(len(type_map[0]) - 1, len(type_map) - 1, 0, 0, wall_pos)
    dalek_sfx = systems.DalekSFXSystem()

    ecs.subscribe("input", ctrl.update)
    ecs.subscribe("move", ai_ctrl.enable)
    ecs.subscribe("move", collision.enable)
    ecs.subscribe("move", movement.enable)
    ecs.subscribe("cancel_move", movement.disable)
    ecs.subscribe("dalek_collision", dalek_sfx.update)

    world.add_system([ai_ctrl, collision, movement, animation, render])

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                break
            if event.type == pg.KEYDOWN:
                ecs.publish("input", world, event.key)

        world.update(clock)
        clock.tick(60)


if __name__ == "__main__":
    main()