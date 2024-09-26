# Py-Dalek
Py-Dalek is a simple 2D game built as a proof of concept for implementing a simple entity-component system (ECS) in Python, using PyGame.

> **Note**: This game is currently not actively maintained and lacks several quality-of-life features such as graceful shutdown, game restarts, and menus.

## Game
In Py-Dalek, you are pursued by enemies known as [Daleks](https://en.wikipedia.org/wiki/Dalek). The objective is to evade the Daleks. If they catch you, you lose. However, if you manage to make the Daleks crash into each other, you win!

### Custom Maps
You can create your own maps for the game. The format follows the [example file](https://github.com/hernadi117/py-dalek/blob/main/map.txt) structure, where:
- `A` represents the Dalek start positions.
- `D` represents the player's start position.
- `*` represents collidable obstacles.
