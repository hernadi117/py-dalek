"""
Author: Victor Hernadi
Last edited: 2023-04-18
"""

from enum import Enum, auto
import pygame as pg
from random import choices
from typing import NamedTuple
from ecs import Component
from components import Animation, Position, Velocity, Renderable, AI, Player

# TODO: Add typehints but my laptop sucks so bad I cannot get any VSCode extensions to work properly.

TileSize = NamedTuple("TileSize", width=int, height=int)
TILE_SIZE = TileSize(16, 16)


class TileType(Enum):
    FLOOR = "."
    HORIZONTAL_EDGE = auto()
    LEFT_VERTICAL_EDGE = auto()
    RIGHT_VERTICAL_EDGE = auto()
    LOWER_LEFT_EDGE = auto()
    LOWER_RIGHT_EDGE = auto()
    WALL = "*"
    SCRAP = "#"
    DOCTOR = "D"
    DALEK = "A"


class LineLengthError(ValueError):
    pass

class InvalidCharacterError(ValueError):
    pass


def read_map_file(file_name: str) -> list[str]:
    """
    Reads the contents of the file with the given file name and returns a list of strings representing the lines in the file.
    
    Parameters:
        file_name (str): The name of the file to read.
    
    Returns:
        A list of strings representing the lines in the file.
    """
    with open(file_name, "r") as f:
        tiles = [line.strip() for line in f]
    return tiles
   

def load_map(file_name: str) -> list[list[TileType]]:
    """
    Loads a map from the file with the given file name and returns a list of lists of TileType values representing the tiles in the map.
    
    Parameters:
        file_name (str): The name of the file to read.
    
    Returns:
        A list of lists of TileType values representing the tiles in the map.
    """
    try:
        raw_map = read_map_file(file_name)
        validate_map(raw_map)
        return parse_map(raw_map, len(raw_map), len(raw_map[0]))
    except IOError as e:
        return f"The file could not be located or accessed."
    except LineLengthError as e:
        return f"All lines must be of equal length. Line {e.args[0]} has invalid length."
    except InvalidCharacterError as e:
        return f"Invalid character '{e.args[2]}' found in column {e.args[1]}, line {e.args[0]}."


def validate_map(raw_map: list[str]) -> list[str]:
    """
    Validates that the given map is well-formed, i.e. that all lines have the same length and that all characters in the map are valid TileType values.
    
    Parameters:
        raw_map (list[str]): A list of strings representing the lines in the map.
    
    Returns:
        A list of strings representing the lines in the map (unchanged).
    
    Raises:
        LineLengthError: If not all lines have the same length.
        InvalidCharacterError: If a character in the map is not a valid TileType value.
    """
    row_count = list(map(len, raw_map))
    for row, count in enumerate(row_count, 1):
        if count != row_count[0]:
            raise LineLengthError(row)
    for row_nr, row in enumerate(raw_map, 1):
        for col_nr, char in enumerate(row, 1):
            if char not in TileType._value2member_map_:
                raise InvalidCharacterError(row_nr, col_nr, char)


def parse_map(raw_map: list[str], rows: int, cols: int) -> list[list[TileType]]:
    """
    Parses a raw map into a 2D array of TileTypes.

    Parameters:
        raw_map (list[str]): A list of strings representing the raw map.
        rows (int): The number of rows in the map.
        cols (int): The number of columns in the map.

    Returns:
        list[list[TileType]]: A 2D array of TileTypes representing the parsed map.
    """
    return [[char_to_tiletype(char, r, c, rows, cols) for c, char in enumerate(row)] for r, row in enumerate(raw_map)]


def char_to_tiletype(char: str, row: int, col: int, max_row: int, max_col: int) -> TileType:
    """
    Converts a character from a raw map into a corresponding TileType.

    Parameters:
        char (str): The character to convert.
        row (int): The row of the character in the map.
        col (int): The column of the character in the map.
        max_row (int): The maximum number of rows in the map.
        max_col (int): The maximum number of columns in the map.

    Returns:
        TileType: The corresponding TileType.
    """
    if char == TileType.WALL.value:
        if row == max_row - 1:
            if col == 0:
                return TileType.LOWER_LEFT_EDGE
            if col == max_col - 1:
                return TileType.LOWER_RIGHT_EDGE
            return TileType.HORIZONTAL_EDGE
        if col == 0:
            return TileType.LEFT_VERTICAL_EDGE
        if col == max_col - 1:
            return TileType.RIGHT_VERTICAL_EDGE
        if row == 0:
            return TileType.HORIZONTAL_EDGE
        return TileType.WALL
    return TileType._value2member_map_[char]


def get_tile_map(tiles: list[list[TileType]]) -> list[list[pg.Surface]]:
    """
    Returns a 2D list of pygame.Surface objects representing the sprites for each tile type.

    Parameters:
        tiles: A 2D list of TileType objects.

    Returns:
        A 2D list of pygame.Surface objects representing the sprites for each tile type.
    """
    sheet = pg.image.load("assets/spritesheet.png").convert_alpha()
    return [[tiletype_to_sprite(sheet, tile) for tile in line] for line in tiles]


def get_player_components(tiles: list[list[TileType]]) -> list[Component]:
    """
    Returns a list of components representing the player's entity.

    Parameters:
        tiles: A 2D list of TileType objects.

    Returns:
        A list of components representing the player's entity.
    """
    sheet = pg.image.load("assets/player_sheet.png").convert_alpha()
    tt = TileSize(48, 48)
    for row_nr, row in enumerate(tiles):
        for col_nr, tile_type in enumerate(row):
            if tile_type == TileType.DOCTOR:
                sprite = get_tile(sheet, tt, (0, 0), (0, 0, tt.width, tt.height), 1)
                return [Position(x=col_nr, y=row_nr), Velocity(0, 0), Renderable(sprite), Player()]
    return []


def get_animated_tile_components(tiles: list[list[TileType]]) -> list[list[Component]]:
    """
    Given a 2D list of TileTypes, returns a 2D list of Components for all tiles
    that have an associated animation sheet. Each inner list contains an Animation,
    a Position, and a Renderable Component.
    
    Parameters:
        tiles (list[list[TileType]]): The 2D list of TileTypes.
        
    Returns:
        list[list[Component]]: The 2D list of Components for animated tiles.
    """
    sheet = pg.image.load("assets/flame_tile_sheet.png").convert_alpha()
    components: list[list[Component]] = []
    for row_nr, row in enumerate(tiles):
        for col_nr, tile_type in enumerate(row):
            if anim_sheet := tiletype_to_animation_sheet(sheet, tile_type):
                components.append([Animation(sheet=anim_sheet, frame_dt=120),
                                   Position(x=col_nr, y=row_nr),
                                   Renderable(sprite=anim_sheet[0])])
    return components


def get_dalek_components(tiles: list[list[TileType]]) -> list[list[Component]]:
    """
    Given a 2D list of TileTypes, returns a 2D list of Components for all Dalek
    tiles. Each inner list contains a Position, a Velocity, a Renderable, and an AI
    Component.
    
    Parameters:
        tiles (list[list[TileType]]): The 2D list of TileTypes.
        
    Returns:
        list[list[Component]]: The 2D list of Components for Dalek tiles.
    """
    sheet = pg.image.load("assets/dalek.png").convert_alpha()
    components: list[list[Component]] = []
    tt = TileSize(48, 48)
    for row_nr, row in enumerate(tiles):
        for col_nr, tile_type in enumerate(row):
            if tile_type == TileType.DALEK:
                sprite = get_tile(sheet, tt, (0, 0), (0, 0, tt.width, tt.height), 1)
                components.append([Position(x=col_nr, y=row_nr), Velocity(0, 0), Renderable(sprite), AI()])
    return components

def get_floor_tile(sheet: pg.Surface, size: TileSize, dest: tuple[int, int], index: int, scale: float = 1) -> pg.Surface:
    """
    Given a spritesheet, the size of a tile, the location of the tile in the spritesheet,
    and the index of the tile, returns a scaled-down Surface object containing the tile image.
    
    Parameters:
        sheet (pg.Surface): The spritesheet containing the tile images.
        size (TileSize): The size of each tile in the spritesheet.
        dest (tuple[int, int]): The location of the tile in the spritesheet, in pixels.
        index (int): The index of the tile in the spritesheet.
        scale (float): The scale factor to apply to the tile image. Default is 1.
        
    Returns:
        pg.Surface: The scaled-down Surface object containing the tile image.
    """
    sprite: pg.Surface = pg.Surface(size).convert_alpha()
    sprite.blit(sheet, dest, (index * size.width, 0, size.width, size.height))
    return pg.transform.scale(sprite, (size.width * scale, size.height * scale))


def get_random_floor_tile(sheet: pg.Surface, size: TileSize, dest: tuple[int, int], scale: float = 1) -> pg.Surface:
    """
    Returns a randomly selected floor tile from a sprite sheet of tiles.

    Parameters:
        sheet (pg.Surface): The sprite sheet of floor tiles.
        size (TileSize): The size of a single tile.
        dest (tuple[int, int]): The destination rectangle where the tile will be blitted onto.
        scale (float, optional): The scale factor to apply to the tile. Defaults to 1.

    Returns:
        pg.Surface: The selected floor tile surface.
    """
    index = choices(list(range(0, 8)), [40] + [1] * 7, k=1)
    return get_floor_tile(sheet, size, dest, *index, scale)


def get_tile(sheet: pg.Surface, size: TileSize, dest: tuple[int, int], area: tuple[int, int, int, int], scale: float = 1) -> pg.Surface:
    """
    Extracts a tile from a sprite sheet using the provided area, and returns it as a scaled surface.

    Parameters:
        sheet (pg.Surface): The sprite sheet containing the tile.
        size (TileSize): The size of the tile.
        dest (tuple[int, int]): The destination rectangle where the tile will be blitted onto.
        area (tuple[int, int, int, int]): The area of the sprite sheet where the tile is located.
        scale (float, optional): The scale factor to apply to the tile. Defaults to 1.

    Returns:
        pg.Surface: The extracted and scaled tile surface.
    """
    sprite: pg.Surface = pg.Surface(size, pg.SRCALPHA).convert_alpha()
    sprite.blit(sheet, dest, area)
    return pg.transform.scale(sprite, (size.width * scale, size.height * scale))


def tiletype_to_sprite(sheet: pg.Surface, tiletype: TileType) -> pg.Surface:
    """
    Returns the sprite surface for a given tile type.

    Parameters:
        sheet (pg.Surface): The sprite sheet to use.
        tiletype (TileType): The tile type to get the sprite for.

    Returns:
        pg.Surface: The sprite surface for the given tile type.
    """
    scale = 3
    match tiletype:
        case TileType.FLOOR:
            return get_random_floor_tile(sheet, TILE_SIZE, (0, 0), scale)
        case TileType.HORIZONTAL_EDGE:
            return get_tile(sheet, TILE_SIZE, (0, 0), (64, 17, TILE_SIZE.width, TILE_SIZE.height), scale)
        case TileType.LEFT_VERTICAL_EDGE:
            return get_tile(sheet, TILE_SIZE, (11, 0), (32, 20, 5, TILE_SIZE.height), scale)
        case TileType.RIGHT_VERTICAL_EDGE:
            return get_tile(sheet, TILE_SIZE, (0, 0), (32, 20, 5, TILE_SIZE.height), scale)
        case TileType.LOWER_LEFT_EDGE:
            return get_tile(sheet, TILE_SIZE, (11, 0), (37, 20, 5, TILE_SIZE.height), scale)
        case TileType.LOWER_RIGHT_EDGE:
            return get_tile(sheet, TILE_SIZE, (0, 0), (37, 20, 5, TILE_SIZE.height), scale)
        case _:
            return get_floor_tile(sheet, TILE_SIZE, (0, 0), 0, scale)


def get_animation_sheet(sheet: pg.Surface, dx: int, scale_x: float = 1, scale_y: float = 1) -> pg.Surface:
    """
    Provides the animation sheet for a particular sheet.

    Parameters:
        sheet (pg.Surface): The sprite sheet to use.
        dx (int): The width of each frame in pixels.
        scale_x (float, optional): The horizontal scale factor for the frames. Defaults to 1.
        scale_y (float, optional): The vertical scale factor for the frames. Defaults to 1.

    Returns:
        list[pg.Surface]: A list of animation frames for the given sprite sheet.
    """
    animation_sheet: pg.Surface = []
    width, height = sheet.get_width(), sheet.get_height()
    for x in range(0, width - 1, dx):
        sprite: pg.Surface = pg.Surface((dx, height), pg.SRCALPHA).convert_alpha()
        sprite.blit(sheet, (0, 0), (x, 0, dx, height))
        animation_sheet.append(pg.transform.scale(sprite, (dx * scale_x, height * scale_y)))
    return animation_sheet

def tiletype_to_animation_sheet(sheet: pg.Surface, tiletype: TileType) -> list[pg.Surface]:
    """
    Returns a list of animation frames for a given tile type.

    Args:
        sheet (pg.Surface): The sprite sheet to use.
        tiletype (TileType): The tile type to get the animation frames for.

    Returns:
        list[pg.Surface]: A list of animation frames for the given tile type.
    """
    match tiletype:
        case TileType.WALL:
            return get_animation_sheet(sheet, 16, 3, 1)
    return []
