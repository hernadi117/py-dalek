import ecs
import systems
from components import AI, Position
import pygame as pg
import utils
from InputBox import InputBox
from Button import Button


def get_initial_map_state(type_map: list[list[utils.TileType]]) -> tuple[list[list[pg.Surface]], list, list[list], list[list], set]:
    """
    This function returns the initial state of the game map based on the given tile type map.

    Parameters:
    type_map (list[list[TileType]]): A 2D list of TileType objects representing the layout of the game map.

    Returns:
    A tuple containing the following items:
        tile_map (list[list[pg.Surface]]): A 2D list of Pygame Surface objects representing the visual appearance of each tile on the game map.
        player_components (list): A list of player character components (e.g. Position, Velocity, Sprite, etc.).
        animated_tiles (list[list]): A nested list of animated tile components (e.g. Position, Velocity, Animation, etc.).
        dalek_components (list[list]): A nested list of Dalek enemy components (e.g. Position, Velocity, Sprite, etc.).
        wall_pos (set): A set of (x, y) tuples representing the coordinates of all wall tiles on the game map.
    """
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


def menu(window) -> list[list[utils.TileType]]:
    """
    Displays the main menu of the game, allowing the user to enter the file path of a map to load.
    Returns a 2D list representing the tile types of the loaded map, or None if the user chooses to quit.

    Args:
        window (pg.Surface): The Pygame surface to display the menu on.

    Returns:
        list[list[TileType]]: A 2D list representing the tile types of the loaded map, or None if the user
            chooses to quit.
    """
    clock = pg.time.Clock()
    pg.font.init()
    input_box = InputBox(210, 70, 140, 32)
    button_play = Button((135, 50), "PLAY", (250, 150))
    button_quit = Button((135, 50), "QUIT", (250, 250))
    done = False
    err_text = ""
    map_txt = "Enter file path of map:"

    while not done:
        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                done = True
            input_box.handle_event(event)
        
        window.fill((30, 30, 30))
        input_box.update()
        input_box.render(window)
        button_play.render(window)
        button_quit.render(window)
        if button_play.clicked(events):
            type_map = utils.load_map(input_box.text.strip())
            if isinstance(type_map, str):
                err_text = type_map
            else:
                return type_map
        if button_quit.clicked(events):
            done = True

        window.blit(pg.font.SysFont('Comic Sans MS', 25).render(map_txt, False, (255, 255, 255)), (210, 40))
        window.blit(pg.font.SysFont('Comic Sans MS', 28).render(err_text, False, (255, 0, 0)), (70, 110))
        pg.display.flip()
        clock.tick(60)


def end_screen(clock, window, won) -> None:
    """
    Displays the end screen of the game, showing a "You won!" message if the player won, and a "You lost!" message
    otherwise. Waits for the player to press any key or click the window's close button before exiting the program.

    Parameters:
        clock (pg.time.Clock): The Pygame clock object used to regulate the frame rate of the game.
        window (pg.Surface): The Pygame surface to display the end screen on.
        won (bool): A boolean flag indicating whether the player won the game or not.

    Returns:
        None
    """
    clicked = False
    while not clicked:
        window.fill((30, 30, 30))
        if won:
            window.blit(pg.font.SysFont('Comic Sans MS', 40).render("You won!", False, (255, 255, 255)), (500, 300))
        else:
            window.blit(pg.font.SysFont('Comic Sans MS', 40).render("You lost!", False, (255, 255, 255)), (500, 300))
        window.blit(pg.font.SysFont('Comic Sans MS', 25).render("Press any key to exit.", False, (255, 255, 255)), (500, 400))
        for event in pg.event.get():
            if event.type == pg.QUIT or event.type == pg.KEYDOWN:
                clicked = True
        pg.display.flip()
        clock.tick(60)


def main() -> None:
    """
    The main game loop.

    Initializes Pygame and the game window, then starts the game loop.
    This loop runs until the game is won or lost, or until the player quits.

    Returns:
        None
    """

    pg.init()
    window = pg.display.set_mode((640, 480))
    type_map = menu(window)
    if type_map is None:
        return
    WIDTH = len(type_map[0])
    HEIGHT = len(type_map)
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
    

    done = False
    won = False
    while not done:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                done = True
            if event.type == pg.KEYDOWN and event.key != pg.K_SPACE:
                # For some reason my PC automatically fires KEYDOWN events on spacebar?
                # Cannot reproduce reliably elsewhere.
                ecs.publish("input", world, event.key)

        world.update(clock, done)
        clock.tick(60)
        won = objective.won
        done = objective.done
        if done:
            end_screen(clock, window, won)

if __name__ == "__main__":
    main()
    pg.quit()