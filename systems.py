from ecs import System, subscribe, publish, World
from components import Position, Velocity, Renderable, Animation
import os
import pygame as pg

class MovementSystem(System):

    def __init__(self) -> None:
        super().__init__()


    def update(self, world: World) -> None:
        for _, (pos, vel) in world.get_component(Position, Velocity):
            print(pos, vel)
            pos.x += vel.x
            pos.y += vel.y


class RenderSystem(System):

    def __init__(self, window: pg.Surface, tile_map: list[list[pg.Surface]]) -> None:
        super().__init__()
        self.window = window
        self.tile_map = tile_map

    
    def create_map(self, width, height):
        return [["." for _ in range(width)] for _ in range(height)]

    def update(self, world: World, *args) -> None:
        for x, tile_row in enumerate(self.tile_map):
            for y, tile in enumerate(tile_row):
                if tile is not None:
                    self.window.blit(tile, (y * tile.get_height(), x * tile.get_width()))
        
        for _, (pos, render) in world.get_component(Position, Renderable):
            if isinstance(render.sprite, pg.Rect):
                pg.draw.rect(self.window, (255, 0, 0), (pos.y, pos.x, 48, 48))
            else:
                self.window.blit(render.sprite, (pos.y * render.sprite.get_height(), pos.x * render.sprite.get_width()))

        pg.display.flip()


class AnimationSystem(System):

    def __init__(self) -> None:
        super().__init__()

    
    def update(self, world: World, dt: pg.time.Clock):
        for _, (anim, render) in world.get_component(Animation, Renderable):
            anim.elapsed += dt.get_time()
            if anim.elapsed >= anim.frame_dt:
                render.sprite = anim.sheet[anim.curr]
                anim.curr += 1
                anim.elapsed = 0
                if anim.curr >= len(anim.sheet):
                    anim.curr = 0


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