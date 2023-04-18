"""
Author: Victor Hernadi
Last edited: 2023-04-18
"""

from ecs import System, publish, World
from components import Position, Velocity, Renderable, Animation, AI, Player
import pygame as pg
from random import random
from utils import get_animation_sheet
from random import randrange

# TODO: Add typehints but my laptop sucks so bad I cannot get any VSCode extensions to work properly.


class MovementSystem(System):
    """
    A system for updating the position of entities based on their velocity.

    This system is responsible for updating the position of entities that have both
    a Position and Velocity component. When enabled, it will add the velocity vector
    to the position of each entity on each update.

    Attributes:
        move (bool): Whether the system is currently enabled to update entity positions.
    """

    def __init__(self) -> None:
        """
        Initialize a new MovementSystem.

        By default, the system is disabled and will not update any entity positions.
        """
        super().__init__()
        self.move = False


    def update(self, world: World, *args) -> None:
        """
        Update the position of entities based on their velocity.

        This method will iterate over all entities in the world that have both a
        Position and Velocity component, and update their position by adding the
        velocity vector to it. If the system is currently disabled, no updates will
        be made.

        Parameters:
            world (World): The world containing the entities to update.
            *args: Any additional arguments passed to the update method. (Unused)
        """
        if not self.move:
            return
        
        for _, (pos, vel) in world.get_component(Position, Velocity):
            pos.x += vel.x
            pos.y += vel.y
        self.move = False
        

    def enable(self):
        """
        Enable the MovementSystem.

        This method sets the 'move' attribute to True, allowing the system to update
        entity positions on subsequent calls to the update method.
        """
        self.move = True

    def disable(self):
        """
        Disable the MovementSystem.

        This method sets the 'move' attribute to False, preventing the system from
        updating entity positions on subsequent calls to the update method.
        """
        self.move = False


class RenderSystem(System):
    """
    A system for rendering entities to a Pygame window.

    This system is responsible for rendering all entities in the world that have
    both a Position and Renderable component. It also renders a fixed background
    tile map to the window.

    Attributes:
        window (pg.Surface): The Pygame window to render to.
        tile_map (list[list[pg.Surface]]): A 2D list of tile surfaces representing the fixed background of the window.
    """

    def __init__(self, window: pg.Surface, tile_map: list[list[pg.Surface]]) -> None:
        """
        Initialize a new RenderSystem.

        Parameters:
            window (pg.Surface): The Pygame window to render to.
            tile_map (list[list[pg.Surface]]): A 2D list of tile surfaces representing
                the fixed background of the window.
        """

        super().__init__()
        self.window = window
        self.tile_map = tile_map
    

    def update(self, world: World, *args) -> None:
        """
        Update the window with the current state of the world.

        This method will render the fixed background tile map to the window, followed
        by all entities in the world that have both a Position and Renderable component.
        Finally, it will flip the display to show the updated window.

        Parameters:
            world (World): The world containing the entities to render.
            *args: Any additional arguments passed to the update method. (Unused)
        """
        for x, tile_row in enumerate(self.tile_map):
            for y, tile in enumerate(tile_row):
                self.window.blit(tile, (y * tile.get_height(), x * tile.get_width()))
        
        for _, (pos, render) in world.get_component(Position, Renderable):
            self.window.blit(render.sprite, (pos.x * render.sprite.get_width(), pos.y * render.sprite.get_height()))

        pg.display.flip()


class AnimationSystem(System):
    """
    A system for playing sprite animations on Renderable entities.

    This system updates the sprites of all entities in the world that have
    both an Animation and Renderable component, based on the elapsed time
    since the last update.
    """

    def __init__(self) -> None:
        """
        Initialize a new AnimationSystem.
        """
        super().__init__()
    
    
    def update(self, world: World, dt: pg.time.Clock, *args):
        """
        Update the sprite animations of all eligible entities in the world.

        This method will update the sprites of all entities in the world that
        have both an Animation and Renderable component. The elapsed time since
        the last update is passed in as the 'dt' parameter.

        Parameters:
            world (World): The world containing the entities to update.
            dt (pg.time.Clock): The time elapsed since the last update.
        """
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
    """
    A system for processing player input and updating entity velocities.

    This system listens for keyboard events and updates the Velocity component
    of the player entity based on the input. It also publishes "move" and "teleport"
    events as appropriate.

    Attributes:
        player (EntityID): The player entity to control.
    """

    def __init__(self, player) -> None:
        """
        Initialize a new InputSystem.

        Parameters:
            player (EntityID): The player entity to control.
        """
        super().__init__()
        self.player = player

    
    def update(self, world: World, key):
        """
        Update the velocity of the player entity based on the given keyboard event.

        This method will update the Velocity component of the player entity based
        on the keyboard event passed in as the 'key' parameter. If the key corresponds
        to a movement direction, the Velocity will be set accordingly and a "move" event
        will be published. If the key corresponds to a teleport action, a "teleport"
        event will be published.

        Parameters:
            world (World): The world containing the entities to update.
            key (int): The Pygame key code for the pressed key.
        """
        
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
    """
    System that handles teleporting the player to a random location within the collision bounds of the game world.
    """
    
    def __init__(self, player_id) -> None:
        """
        Initializes the TeleportSystem instance.

        Parameters:
            player_id (int): The entity ID of the player.
        """
        super().__init__()
        self.player_id = player_id


    def update(self, world: World):
        """
        Updates the TeleportSystem instance by teleporting the player to a random location within the collision bounds
        of the game world.

        Parameters:
            world (World): The game world.
        """
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
    """
    A system that handles collisions between entities and the game boundaries and walls.

    Attributes:
        max_x (int): The maximum x-coordinate of the game world.
        max_y (int): The maximum y-coordinate of the game world.
        min_x (int): The minimum x-coordinate of the game world.
        min_y (int): The minimum y-coordinate of the game world.
        walls (set): A set of coordinates representing the locations of walls in the game world.
        scraps (set): A set of coordinates representing the locations of scraps in the game world.
        move (bool): Flag if the system is active or not this frame.
    """
    def __init__(self, max_x, max_y, min_x, min_y, walls) -> None:
        """
        Initializes a new instance of the CollisionSystem class.

        Parameters:
            max_x (int): The maximum x-coordinate of the game world.
            max_y (int): The maximum y-coordinate of the game world.
            min_x (int): The minimum x-coordinate of the game world.
            min_y (int): The minimum y-coordinate of the game world.
            walls (set): A set of coordinates representing the locations of walls in the game world.
        """
        super().__init__()
        self.max_x = max_x
        self.max_y = max_y
        self.min_x = min_x
        self.min_y = min_y
        self.walls = walls
        self.scraps = set()
        self.move = False

    
    def update(self, world: World, *args):
        """
        Updates the CollisionSystem based on the current state of the game world.

        Parameters:
            world (World): The game world to update.
            *args: Optional arguments to the update method.
        """
        if not self.move:
            return

        player_id, (pos, vel, _) = world.get_component(Position, Velocity, Player)[0]
        if not self.valid_move(x := pos.x + vel.x, y := pos.y + vel.y) or (x, y) in self.scraps:
            publish("cancel_move")
            return

        entity_collision = {}
        occupied = {}
        for entity_id, (pos, vel) in world.get_component(Position, Velocity):
            if entity_id != player_id and not self.valid_move(pos.x + vel.x, pos.y + vel.y):
                self.wall_slide_handler(pos, vel)
                if vel.x == 0 and vel.y == 0:
                    if (pos.x, pos.y) not in occupied:
                        occupied[(pos.x, pos.y)] = entity_id
                    else:
                        entity_collision[(entity_id, occupied[(pos.x, pos.y)])] = (pos.x, pos.y)
                    continue
            x, y = pos.x + vel.x, pos.y + vel.y
            if (x, y) in self.scraps:
                entity_collision[(entity_id, entity_id)] = (x, y)
            elif (x, y) not in occupied:
                occupied[(x, y)] = entity_id
            else:
                entity_collision[(entity_id, occupied[(x, y)])] = (x, y)
        self.handle_entity_collision(world, entity_collision, player_id)
        self.move = False


    def wall_slide_handler(self, pos: Position, vel: Velocity) -> None:
        """
        This method handles sliding a Dalek along a wall when they hit it. 
        This method only updates the velocity components of the Dalek, if they are moving in a diagonal direction along a wall,
        but only if the wall slide is possible, i.e., the next position is still valid.

        Parameters:
            pos (Position): The current position of the Dalek.
            vel (Velocity): The current velocity of the Dalek.

        Returns:
            None
        """
        x = pos.x + vel.x
        y = pos.y + vel.y
        if vel.x > 0 and vel.y < 0:
            if self.valid_move(x, pos.y):
                vel.y = 0
            if self.valid_move(pos.x, y):
                vel.x = 0
        elif vel.x < 0 and vel.y < 0:
            if self.valid_move(x, pos.y):
                vel.y = 0
            if self.valid_move(pos.x, y):
                vel.x = 0
        elif vel.x < 0 and vel.y > 0:
            if self.valid_move(x, pos.y):
                vel.y = 0
            if self.valid_move(pos.x, y):
                vel.x = 0
        elif vel.x > 0 and vel.y > 0:
            if self.valid_move(x, pos.y):
                vel.y = 0
            if self.valid_move(pos.x, y):
                vel.x = 0
        else:
            vel.x = 0
            vel.y = 0


    def handle_entity_collision(self, world: World, collision, player_id):
        """
        Handles collisions between entities in the game world.

        Parameters:
            world (World): The game world.
            collision (dict): A dictionary containing the entities involved in each collision and their coordinates.
            player_id (int): The ID of the player entity.
        """
        dalek_collisions = []
        for entities, (x, y) in collision.items():
            if player_id in entities:
                publish("game_over", world)
            if entities[0] == entities[1]:
                publish("scrap_collision", world, (Position(x, y),))
            else:
                dalek_collisions.append(Position(x, y))
            world.mark_entity_for_removal(entities)
        self.add_scrap(dalek_collisions)
        publish("dalek_collision", world, dalek_collisions)


    def within_map(self, x: int, y: int) -> bool:
        """
        Checks if coordinates are within the map boundaries.

        Parameters:
            x: x-coordinate
            y: y-coordinate
        """
        return self.min_x < x < self.max_x and self.min_y < y < self.max_y


    def collide_wall(self, x: int, y: int) -> bool:
        """
        Checks if coordinates overlap with a wall.

        Parameters:
            x: x-coordinate
            y: y-coordinate
        """
        return (x, y) in self.walls


    def valid_move(self, x: int, y: int) -> bool:
        """
        Checks if coordinates is a valid position to mvoe to.

        Parameters:
            x: x-coordinate
            y: y-coordinate
        """
        return self.within_map(x, y) and not self.collide_wall(x, y)

    def enable(self) -> None:
        """
        Enable this system to work on subsequent calls to the update method.
        """
        self.move = True

    
    def add_scrap(self, pos: list[Position]) -> None:
        """
        Adds scraps to be collidable and thus objects for collision.

        Parameters:
            pos: list of Position (x, y) coordinates
        """
        for p in pos:
            self.scraps.add((p.x, p.y))


class EnemyControl(System):
    """
    The EnemyControl updates the positions of AI entities
    based on the position of the Player entity.
    """

    def __init__(self) -> None:
        """
        Initializes an instance of the EnemyControl class.
        """
        super().__init__()
        self.move = False

    
    def update(self, world: World, *args):
        """
        Updates the positions of AI entities based on the position of the Player entity.
        
        Parameters:
            world (World): the game world to update
            *args: additional arguments to pass to the method (not used in this implementation)
        """
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
        """
        Calculates the direction for an AI entity to move based on its current position and
        the position of the Player entity.
        
        Args:
            pos_x (int): the x-coordinate of the current position of the AI entity
            pos_y (int): the y-coordinate of the current position of the AI entity
            target_x (int): the x-coordinate of the current position of the Player entity
            target_y (int): the y-coordinate of the current position of the Player entity
        
        Returns:
            Tuple: a tuple containing the x and y components of the direction the AI entity should move
        """
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
        """
        Enables the EnemyControl system to update the positions of AI entities.
        """
        self.move = True


class DalekSFXSystem(System):
    """
    A system that creates a visual explosion effect when Daleks are destroyed.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance of the DalekSFXSystem class.
        """
        super().__init__()
        self.anim_sheet = get_animation_sheet(pg.image.load("assets/explosion_sheet.png").convert_alpha(), 48, 1, 1)
        

    def update(self, world: World, positions: list[Position]):
        """
        Updates the DalekSFXSystem.

        Parameters:
            world: The game world.
            positions: A list of Position objects representing the positions of Daleks that were destroyed.
        """
        for pos in positions:
            world.add_entity(Position(x=pos.x, y=pos.y),
                            Animation(sheet=self.anim_sheet, frame_dt=60, once=True),
                            Renderable(self.anim_sheet[0]))
            

class DalekScrapSystem(System):
    """
    A system that handles creating Dalek scrap and their animations when Daleks are destroyed.

    Attributes:
    anim_sheet (list[Surface]): The sprite sheet containing the animation frames.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance of the DalekScrapSystem class.
        """   
        super().__init__()
        self.anim_sheet = get_animation_sheet(pg.image.load("assets/dalek_scrap_sheet.png").convert_alpha(), 48, 1, 1)


    def update(self, world: World, positions: list[Position]):
        """
        Update the system by creating Dalek scrap animations at the positions of destroyed Daleks.

        Parameters:
        world (World): The game world.
        positions (list[Position]): The positions of the destroyed Daleks.
        """
        for pos in positions:
            world.add_entity(Position(x=pos.x, y=pos.y),
                            Animation(sheet=self.anim_sheet, frame_dt=60),
                            Renderable(self.anim_sheet[0]))
            

class GameObjectiveSystem(System):
    """
    A system that handles game objectives, such as winning and losing the game.
    Attributes:
    done (bool): True if the game is over, else False
    won (bool): True if the player won, else False
    """
    def __init__(self) -> None:
        """
        Initializes a new instance of the GameObjectiveSystem class.
        """   
        super().__init__()
        self.won = False
        self.done = False
    

    def update(self, world: World, *args):
        """
        Update the system by checking if the player has won or lost the game.

        Parameters:
            world (World): The game world.
            *args: Additional arguments (not used).
        """

        if not world.get_component(AI):
            self.done = True
            self.won = True
    

    def lost_game(self, world):
        """
        Terminate the game when the player loses.

        Parameters:
        world (World): The game world.
        """
        self.done = True
        self.won = False
