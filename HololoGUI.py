import pygame
from pygame.locals import *
import pyassimp

# Initialization of Window
width, height = 1280, 720
pygame.init()
window = pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
pygame.display.set_caption("Hololo")

# Testing and Importing Meshes With Assimp (https://www.assimp.org)
scene = pyassimp.load("Template/cube.stl")
model_normals = scene.meshes[0].normals
model_vertices = scene.meshes[0].vertices


# Main Loop
running = True
while running:
	pygame.display.flip()
	pygame.time.wait(10)

pygame.quit()