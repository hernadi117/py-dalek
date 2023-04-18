import pygame as pg

class Button:
    def __init__(self, size, text, pos, bgColor=(255, 255, 255), textColor=(0, 0, 0)):
        self.pos  = pos
        self.size = size
        self.text = text
        self.font = pg.font.Font(pg.font.get_default_font(), size[1])
        self.textSurf = self.font.render(f"{text}", True, textColor)
        self.button = pg.Surface((size[0], size[1])).convert()
        self.button.fill(bgColor)

    def render(self, window):
        window.blit(self.button, (self.pos[0], self.pos[1]))
        window.blit(self.textSurf, (self.pos[0]+1, self.pos[1]+5))

    def clicked(self, events):
        mousePos = pg.mouse.get_pos()
        for event in events:
            if self.button.get_rect(topleft=self.pos).collidepoint(mousePos[0], mousePos[1]):
                if event.type == pg.MOUSEBUTTONDOWN:
                    return True
        return False