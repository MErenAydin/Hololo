import pygame
import moderngl
from .Settings import Settings
from pygame.locals import *
import ctypes

# Set DPI Awareness
errorCode = ctypes.windll.shcore.SetProcessDpiAwareness(2)

settings = Settings()
pygame.init()

pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)

window = pygame.display.set_mode((settings.width, settings.height), DOUBLEBUF | OPENGL)
pygame.display.set_caption("Hololo")

context = moderngl.create_context(require=330)
context.enable(moderngl.DEPTH_TEST)
context.enable(moderngl.BLEND)
context.enable(moderngl.CULL_FACE)
context.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)