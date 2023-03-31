import ecs
import systems
from components import Position
import pygame as pg
import utils


def get_initial_map_state(type_map: str):
    tile_map = utils.get_tile_map(type_map)
    player_components = utils.get_player_components(type_map)
    animated_tiles = utils.get_animated_tile_components(type_map)
    dalek_components = utils.get_dalek_components(type_map)
    wall_pos = set()
    for comps in animated_tiles:
        for comp in comps:
            if isinstance(comp, Position):
                wall_pos.add((comp.x, comp.y))
    return tile_map, player_components, animated_tiles, dalek_components, wall_pos
    

def main():

    type_map = utils.load_map("map.txt")
    WIDTH = len(type_map[0])
    HEIGHT = len(type_map)
    pg.init()
    window = pg.display.set_mode((WIDTH * 16 * 3, HEIGHT * 16 * 3), pg.DOUBLEBUF)
    pg.display.set_caption("Best Game")
    clock = pg.time.Clock()
    
    tile_map, player_components, animated_tiles, dalek_components, wall_pos = get_initial_map_state(type_map)
    world = ecs.World()
    
    player_id = world.add_entity(*player_components)
    ctrl = systems.InputSystem(player_id)
    movement = systems.MovementSystem()
    render = systems.RenderSystem(window, tile_map)
    animation = systems.AnimationSystem()
    ai_ctrl = systems.EnemyControl()
    objective = systems.GameObjectiveSystem()

    for comps in animated_tiles:
        world.add_entity(*comps)
    
    for comps in dalek_components:
        world.add_entity(*comps)
    
    
    collision = systems.CollisionSystem(WIDTH - 1, HEIGHT - 1, 0, 0, wall_pos)
    dalek_sfx = systems.DalekSFXSystem()
    scrap_system = systems.DalekScrapSystem()
    teleport = systems.TeleportSystem(player_id)

    world.add_system([objective, ai_ctrl, collision, movement, animation, render])

    ecs.subscribe("input", ctrl.update)
    ecs.subscribe("move", ai_ctrl.enable)
    ecs.subscribe("move", collision.enable)
    ecs.subscribe("move", movement.enable)
    ecs.subscribe("cancel_move", movement.disable)
    ecs.subscribe("dalek_collision", dalek_sfx.update)
    ecs.subscribe("scrap_collision", dalek_sfx.update)
    ecs.subscribe("dalek_collision", scrap_system.update)
    ecs.subscribe("teleport", teleport.update)
    ecs.subscribe("game_over", objective.lost_game)
    

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                break
            if event.type == pg.KEYDOWN and event.key != pg.K_SPACE:
                # For some reason my PC automatically fires KEYDOWN events on spacebar?
                # Cannot reproduce reliably elsewhere.
                ecs.publish("input", world, event.key)

        world.update(clock)
        clock.tick(60)


if __name__ == "__main__":
    main()