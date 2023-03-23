import pygame as pg
import moderngl as mgl
import numpy as np
import sys

class Game:
    def __init__(self) -> None:
        pg.init()
        self.win_size = (1600, 900);
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK, pg.GL_CONTEXT_PROFILE_CORE)
        pg.display.set_mode(self.win_size, pg.OPENGL | pg.DOUBLEBUF)
        self.clock = pg.time.Clock()
        self.context = mgl.create_context()
        self.scene = Triangle(self)


    def check_event(self) -> None:
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                self.scene.destroy()
                pg.quit()
                sys.exit(0)

    def render(self):
        self.context.clear(color=(0.08, 0.16, 0.18))
        self.scene.render()
        pg.display.flip()

    def run(self):
        while True:
            self.check_event()
            self.render()
            self.clock.tick(60)


class Triangle:
    
    def __init__(self, app):
        self.app = app
        self.context : mgl.Context = app.context

        self.vertices = (
            -0.5, -0.5, 0.0,
            0.5, -0.5, 0.0,
            0.0, 0.5, 0.5
        )
        self.vertices = np.array(self.vertices, dtype=np.float32)
        self.vbo = self.context.buffer(self.vertices)
        self.shader_program = self.get_shader_program("default")
        self.vao = self.get_vao()


    def render(self):
        self.vao.render()

    def destroy(self):
        self.vbo.release()
        self.shader_program.release()
        self.vao.release()

    def get_shader_program(self, shader_name):
        with open(f"shaders/{shader_name}.vert") as f:
            vertex_shader = f.read()
        
        with open(f"shaders/{shader_name}.frag") as f:
            fragment_shader = f.read()
        
        program = self.context.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)
        return program

    def get_vao(self):
        vao = self.context.vertex_array(self.shader_program, [(self.vbo, "3f", "in_position")])
        return vao

if __name__ == "__main__":
    app = Game()
    app.run()