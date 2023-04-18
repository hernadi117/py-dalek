"""
Author: Victor Hernadi
Last edited: 2023-04-18
"""

import pygame as pg

class InputBox:

    def __init__(self, x, y, width, height, text=""):

        self.rect = pg.Rect(x, y, width, height)
        self.inactive_color = pg.Color('grey')
        self.active_color = pg.Color('white')
        self.color = self.inactive_color
        self.font = pg.font.Font(None, 32)
        self.text = text
        self.surface = self.font.render(text, True, self.inactive_color)
        self.active = False

    def handle_event(self, event):

        if event.type == pg.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            
            self.color = self.active_color if self.active else self.inactive_color
            
        
        if event.type == pg.KEYDOWN:
            if self.active:
                if event.key == pg.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                
            self.surface = self.font.render(self.text, True, self.color)

    def update(self):
        width = max(200, self.surface.get_width()+10)
        self.rect.w = width
        
    def render(self, window):
        window.blit(self.surface, (self.rect.x+5, self.rect.y+5))
        pg.draw.rect(window, self.color, self.rect, 2)

        