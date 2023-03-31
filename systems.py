from ecs import System, subscribe, publish, World
from components import Position, Velocity, Renderable, Animation, AI, Player
import pygame as pg
from random import random
from utils import get_animation_sheet
from random import randrange


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
                        world.mark_entity_for_removal((entity_id,))
                    else:
                        anim.curr = 0


class InputSystem(System):

    def __init__(self, player) -> None:
        super().__init__()
        self.player = player

    
    def update(self, world: World, key):
        
        for vel in world.component_for(self.player, Velocity):
            if key == pg.K_LEFT:
                vel.x = -1
                vel.y = 0
                publish("move")
            elif key == pg.K_RIGHT:
                vel.x = 1
                vel.y = 0
                publish("move")
            elif key == pg.K_UP:
                vel.x = 0
                vel.y = -1
                publish("move")
            elif key == pg.K_DOWN:
                vel.x = 0
                vel.y = 1
                publish("move")
            elif key == pg.K_x:
                publish("teleport", world)
                publish("move")
            


class TeleportSystem(System):
    
    def __init__(self, player_id) -> None:
        super().__init__()
        self.player_id = player_id


    def update(self, world: World):
        collisions = world.get_system(CollisionSystem)
        pos = world.component_for(self.player_id, Position)[0]
        while True:
            x = randrange(collisions.min_x, collisions.max_x)
            y = randrange(collisions.min_y, collisions.max_y)
            if collisions.valid_move(x, y) and (x, y) not in collisions.scraps:
                pos.x = x
                pos.y = y
                break



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
        if not self.valid_move(x := pos.x + vel.x, y := pos.y + vel.y) or (x, y) in self.scraps:
            publish("cancel_move")
            return

        entity_collision = {}
        occupied = {}
        for entity_id, (pos, vel) in world.get_component(Position, Velocity):
            x, y = pos.x + vel.x, pos.y + vel.y
            if not self.valid_move(x, y):
                vel.x = 0
                vel.y = 0
            elif (x, y) in self.scraps:
                entity_collision[(entity_id, entity_id)] = (x, y)
            elif (x, y) not in occupied:
                occupied[(x, y)] = entity_id
            else:
                entity_collision[(entity_id, occupied[(x, y)])] = (x, y)
        self.handle_entity_collision(world, entity_collision, player_id)
        self.move = False

    def handle_entity_collision(self, world: World, collision, player_id):
        dalek_collisions = []
        for entities, (x, y) in collision.items():
            if player_id in entities:
                publish("game_over", world)
            elif entities[0] == entities[1]:
                publish("scrap_collision", world, (Position(x, y),))
            else:
                dalek_collisions.append(Position(x, y))
            world.mark_entity_for_removal(entities)
        self.add_scrap(dalek_collisions)
        publish("dalek_collision", world, dalek_collisions)


    def within_map(self, x, y) -> bool:
        return self.min_x < x < self.max_x and self.min_y < y < self.max_y


    def collide_wall(self, x: int, y: int) -> bool:
        return (x, y) in self.walls


    def valid_move(self, x: int, y: int) -> bool:
        return self.within_map(x, y) and not self.collide_wall(x, y)

    def enable(self) -> None:
        self.move = True

    
    def add_scrap(self, pos: list[Position]) -> None:
        for p in pos:
            self.scraps.add((p.x, p.y))


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
        self.anim_sheet = get_animation_sheet(pg.image.load("assets/explosion_sheet.png").convert_alpha(), 48, 1, 1)
        

    def update(self, world: World, positions: list[Position]):
        for pos in positions:
            world.add_entity(Position(x=pos.x, y=pos.y),
                            Animation(sheet=self.anim_sheet, frame_dt=60, once=True),
                            Renderable(self.anim_sheet[0]))
            

class DalekScrapSystem(System):

    def __init__(self) -> None:
        super().__init__()
        self.anim_sheet = get_animation_sheet(pg.image.load("assets/dalek_scrap_sheet.png").convert_alpha(), 48, 1, 1)


    def update(self, world: World, positions: list[Position]):
        for pos in positions:
            world.add_entity(Position(x=pos.x, y=pos.y),
                            Animation(sheet=self.anim_sheet, frame_dt=60),
                            Renderable(self.anim_sheet[0]))
            

class GameObjectiveSystem(System):
    
    def __init__(self) -> None:
        super().__init__()
    

    def update(self, world: World, *args):

        # TODO: Add game termination.

        if not world.get_component(AI):
            print("You won.")
            pg.quit()
    

    def lost_game(self, world):
        # TODO: Add game termination.
        print("Game over.")
        pg.quit()
        
