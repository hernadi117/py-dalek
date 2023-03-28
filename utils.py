from tiles import TileType

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
