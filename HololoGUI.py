import pygame
from pygame.locals import *

width, height = 1280, 720

pygame.init()
pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)


while True:
	pygame.display.flip()
	pygame.time.wait(10)