from ecs import System, subscribe, publish, World
from components import Position, Velocity, Renderable, Animation, AI, Player
import pygame as pg
from random import random
from tiles import get_animation_sheet


class MovementSystem(System):

    def __init__(self) -> None:
        super().__init__()
        self.move = False


    def update(self, world: World, *args) -> None:
        if not self.move:
            return
        
        for _, (pos, vel) in world.get_component(Position, Velocity):
            pos.x += vel.x
            pos.y += vel.y
        self.move = False
        

    def enable(self):
        self.move = True

    def disable(self):
        self.move = False


class RenderSystem(System):

    def __init__(self, window: pg.Surface, tile_map: list[list[pg.Surface]]) -> None:
        super().__init__()
        self.window = window
        self.tile_map = tile_map
    

    def update(self, world: World, *args) -> None:
        for x, tile_row in enumerate(self.tile_map):
            for y, tile in enumerate(tile_row):
                self.window.blit(tile, (y * tile.get_height(), x * tile.get_width()))
        
        for _, (pos, render) in world.get_component(Position, Renderable):
            self.window.blit(render.sprite, (pos.x * render.sprite.get_width(), pos.y * render.sprite.get_height()))

        pg.display.flip()


class AnimationSystem(System):

    def __init__(self) -> None:
        super().__init__()

    
    def update(self, world: World, dt: pg.time.Clock):
        for entity_id, (anim, render) in world.get_component(Animation, Renderable):
            anim.elapsed += dt.get_time()
            if anim.elapsed >= anim.frame_dt:
                render.sprite = anim.sheet[anim.curr]
                anim.curr += 1
                anim.elapsed = 0
                if anim.curr >= len(anim.sheet):
                    if anim.once:
                        world.to_remove(entity_id)
                    else:
                        anim.curr = 0


class InputSystem(System):

    def __init__(self, player) -> None:
        super().__init__()
        self.player = player

    
    def update(self, world: World, direction):
        
        for vel in world.component_for(self.player, Velocity):
            if direction == pg.K_LEFT:
                    vel.x = -1
                    vel.y = 0
            if direction == pg.K_RIGHT:
                    vel.x = 1
                    vel.y = 0
            if direction == pg.K_UP:
                    vel.x = 0
                    vel.y = -1
            if direction == pg.K_DOWN:
                    vel.x = 0
                    vel.y = 1
            publish("move")


class CollisionSystem(System):
    def __init__(self, max_x, max_y, min_x, min_y, walls) -> None:
        super().__init__()
        self.max_x = max_x
        self.max_y = max_y
        self.min_x = min_x
        self.min_y = min_y
        self.walls = walls
        self.scraps = set()
        self.move = False

    
    def update(self, world: World, *args):
        if not self.move:
            return

        player_id, (pos, vel, _) = world.get_component(Position, Velocity, Player)[0]
        if not self.valid_move(pos.x + vel.x, pos.y + vel.y):
            publish("cancel_move")
            return

        collision = {}
        occupied = {}
        for entity_id, (pos, vel) in world.get_component(Position, Velocity):
            x, y = pos.x + vel.x, pos.y + vel.y
            if not self.valid_move(x, y):
                vel.x = 0
                vel.y = 0
            elif (x, y) not in occupied:
                occupied[(x, y)] = entity_id
            else:
                collision[(entity_id, occupied[(x, y)])] = (x, y)
        
        self.handle_entity_collision(world, collision, player_id)
        self.move = False

    def handle_entity_collision(self, world: World, collision, player_id):
        dalek_collisions = []
        for entities, (x, y) in collision.items():
            if player_id in entities:
                print("game over")
                #publish("game_over")
                world.mark_entity_for_removal(entities)
            dalek_collisions.append(Position(x, y))
        self.add_scrap(dalek_collisions)
        publish("dalek_collision", world, dalek_collisions)

    


    def within_map(self, x, y) -> bool:
        return self.min_x < x < self.max_x and self.min_y < y < self.max_y


    def collide_wall(self, x: int, y: int) -> bool:
        return (x, y) in self.walls


    def valid_move(self, x, y):
        return self.within_map(x, y) and not self.collide_wall(x, y)

    def enable(self):
        self.move = True

    
    def add_scrap(self, *pos):
        for p in pos:
            self.scrap.add((p.x, p.y))


class EnemyControl(System):

    def __init__(self) -> None:
        super().__init__()
        self.move = False

    
    def update(self, world: World, *args):
        if not self.move:
            return
        
        pos, vel, _ = world.get_component(Position, Velocity, Player)[0][1]
        target = (pos.x + vel.x, pos.y + vel.y)
        
        for _, (pos, vel, _) in world.get_component(Position, Velocity, AI):
            vx, vy = self.direction_to_go(pos.x, pos.y, target[0], target[1])
            vel.x = vx
            vel.y = vy

        self.move = False

    
    def direction_to_go(self, pos_x: int, pos_y: int, target_x: int, target_y: int):
        dx, dy = pos_x - target_x, pos_y - target_y
        vx = (dx < 0) - (dx > 0)
        vy = (dy < 0) - (dy > 0) 

        if not ((adx := abs(dx)) == (ady := abs(dy)) or adx == 0 or ady == 0):
            r = random()
            q = adx / ady
            if q < 1 and r > q:
                vx = 0
            if q > 1 and r > 1 / q:
                vy = 0
        return vx, vy

    def enable(self):
        self.move = True


class DalekSFXSystem(System):

    def __init__(self) -> None:
        super().__init__()
        self.anim_sheet = get_animation_sheet(pg.image.load("assets/flame_tile_sheet.png").convert_alpha(), 16, 3)
        

    def update(self, world: World, positions: list[Position]):
        for pos in positions:
            world.add_entity(Position(x=pos.x, y=pos.y),
                            Animation(sheet=self.anim_sheet, frame_dt=60, once=True),
                            Renderable(self.anim_sheet[0]))
            

class DalekScrapSystem(System):

    def __init__(self) -> None:
        super().__init__()
        self.sprite = ...


    def update(self, world: World, pos):
        pass
            