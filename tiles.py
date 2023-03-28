from enum import Enum, auto
import pygame as pg
from random import choices
from typing import NamedTuple
from ecs import Component
from components import Animation, Position, Renderable

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


def get_tile_map(tiles: list[list[TileType]]) -> list[list[pg.Surface]]:
    sheet = pg.image.load("assets/spritesheet.png").convert_alpha()
    return [[tiletype_to_sprite(sheet, tile) for tile in line] for line in tiles]


def get_animated_tile_components(tiles: list[list[TileType]]) -> list[list[Component]]:
    sheet = pg.image.load("assets/flame_tile_sheet.png").convert_alpha()
    components: list[list[Component]] = []
    for row_nr, row in enumerate(tiles):
        for col_nr, tile_type in enumerate(row):
            if anim_sheet := tiletype_to_animation_sheet(sheet, tile_type):
                components.append([Animation(sheet=anim_sheet, frame_dt=120), Position(x=row_nr, y=col_nr), Renderable(sprite=anim_sheet[0])])
    return components

def get_floor_tile(sheet: pg.Surface, size: TileSize, dest: tuple[int, int], index: int, scale: float = 1) -> pg.Surface:
    sprite: pg.Surface = pg.Surface(size).convert_alpha()
    sprite.blit(sheet, dest, (index * size.width, 0, size.width, size.height))
    return pg.transform.scale(sprite, (size.width * scale, size.height * scale))


def get_random_floor_tile(sheet: pg.Surface, size: TileSize, dest: tuple[int, int], scale: float = 1) -> pg.Surface:
    index = choices(list(range(0, 8)), [40] + [1] * 7, k=1)
    return get_floor_tile(sheet, size, dest, *index, scale)


def get_tile(sheet: pg.Surface, size: TileSize, dest: tuple[int, int], area: tuple[int, int, int, int], scale: float = 1) -> pg.Surface:
    sprite: pg.Surface = pg.Surface(size).convert_alpha()
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
            return get_random_floor_tile(sheet, TILE_SIZE, (0, 0), scale)


def get_animation_sheet(sheet: pg.Surface, dx: int, scale: float = 1) -> pg.Surface:
    animation_sheet: pg.Surface = []
    width, height = sheet.get_width(), sheet.get_height()
    for x in range(0, width - 1, dx):
        sprite: pg.Surface = pg.Surface((dx, height)).convert_alpha()
        sprite.blit(sheet, (0, 0), (x+1, 0, dx, height))
        animation_sheet.append(pg.transform.scale(sprite, (dx * scale, height * scale / 3)))
    return animation_sheet

def tiletype_to_animation_sheet(sheet: pg.Surface, tiletype: TileType) -> list[pg.Surface]:
    match tiletype:
        case TileType.WALL:
            return get_animation_sheet(sheet, 16, 3)
    return []