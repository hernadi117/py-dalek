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
    with open(file_name, "r") as f:
        tiles = [line.strip() for line in f]
    return tiles
   

def load_map(file_name: str) -> list[list[TileType]]:
    try:
        raw_map = read_map_file(file_name)
        validate_map(raw_map)
        return parse_map(raw_map, len(raw_map), len(raw_map[0]))
    except IOError as e:
        print(e)
    except LineLengthError as e:
        print(f"All lines must be of equal length. Line {e.args[0]} has invalid length.")
    except InvalidCharacterError as e:
        print(f"Invalid character '{e.args[2]}' found in column {e.args[1]}, line {e.args[0]}.")


def validate_map(raw_map: list[str]) -> list[str]:
    row_count = list(map(len, raw_map))
    for row, count in enumerate(row_count, 1):
        if count != row_count[0]:
            raise LineLengthError(row)
    for row_nr, row in enumerate(raw_map, 1):
        for col_nr, char in enumerate(row, 1):
            if char not in TileType._value2member_map_:
                raise InvalidCharacterError(row_nr, col_nr, char)


def parse_map(raw_map: list[str], rows: int, cols: int) -> list[list[TileType]]:
    return [[char_to_tiletype(char, r, c, rows, cols) for c, char in enumerate(row)] for r, row in enumerate(raw_map)]


def char_to_tiletype(char: str, row: int, col: int, max_row: int, max_col: int) -> TileType:
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
    sheet = pg.image.load("assets/spritesheet.png").convert_alpha()
    return [[tiletype_to_sprite(sheet, tile) for tile in line] for line in tiles]


def get_player_components(tiles: list[list[TileType]]) -> list[Component]:
    sheet = pg.image.load("assets/player_sheet.png").convert_alpha()
    tt = TileSize(48, 48)
    for row_nr, row in enumerate(tiles):
        for col_nr, tile_type in enumerate(row):
            if tile_type == TileType.DOCTOR:
                sprite = get_tile(sheet, tt, (0, 0), (0, 0, tt.width, tt.height), 1)
                return [Position(x=col_nr, y=row_nr), Velocity(0, 0), Renderable(sprite), Player()]
    return []


def get_animated_tile_components(tiles: list[list[TileType]]) -> list[list[Component]]:
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
    sprite: pg.Surface = pg.Surface(size).convert_alpha()
    sprite.blit(sheet, dest, (index * size.width, 0, size.width, size.height))
    return pg.transform.scale(sprite, (size.width * scale, size.height * scale))


def get_random_floor_tile(sheet: pg.Surface, size: TileSize, dest: tuple[int, int], scale: float = 1) -> pg.Surface:
    index = choices(list(range(0, 8)), [40] + [1] * 7, k=1)
    return get_floor_tile(sheet, size, dest, *index, scale)


def get_tile(sheet: pg.Surface, size: TileSize, dest: tuple[int, int], area: tuple[int, int, int, int], scale: float = 1) -> pg.Surface:
    sprite: pg.Surface = pg.Surface(size, pg.SRCALPHA).convert_alpha()
    sprite.blit(sheet, dest, area)
    return pg.transform.scale(sprite, (size.width * scale, size.height * scale))


def tiletype_to_sprite(sheet: pg.Surface, tiletype: TileType) -> pg.Surface:
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
    animation_sheet: pg.Surface = []
    width, height = sheet.get_width(), sheet.get_height()
    for x in range(0, width - 1, dx):
        sprite: pg.Surface = pg.Surface((dx, height), pg.SRCALPHA).convert_alpha()
        sprite.blit(sheet, (0, 0), (x, 0, dx, height))
        animation_sheet.append(pg.transform.scale(sprite, (dx * scale_x, height * scale_y)))
    return animation_sheet

def tiletype_to_animation_sheet(sheet: pg.Surface, tiletype: TileType) -> list[pg.Surface]:
    match tiletype:
        case TileType.WALL:
            return get_animation_sheet(sheet, 16, 3, 1)
    return []
