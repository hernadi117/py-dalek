"""
Author: Victor Hernadi
Last edited: 2023-04-18
"""

import pygame as pg

class Button:
    def __init__(self, width, height, text, pos, background_color=(255, 255, 255), text_color=(0, 0, 0)):
        self.width = width
        self.height = height
        self.x = pos[0]
        self.y = pos[1]
        self.text = text
        self.font = pg.font.Font(pg.font.get_default_font(), height)
        self.text_surface = self.font.render(text, True, text_color)
        self.button = pg.Surface((width, height)).convert()
        self.button.fill(background_color)

    def render(self, window):
        window.blit(self.button, (self.x, self.y))
        window.blit(self.text_surface, (self.x+1, self.y+5))

    def clicked(self, events):
        for event in events:
            if event.type == pg.MOUSEBUTTONDOWN:
                if self.button.get_rect(topleft=(self.x, self.y)).collidepoint(event.pos):
                    return True
        return False