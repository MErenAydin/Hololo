import pygame
from pygame.locals import *
import pyassimp

class Mesh:
	def __init__(self, scene, x = 0, y = 0, z = 0, scale = 1, mesh_index = 0):
		self.scene = scene
		self.normals = scene.meshes[mesh_index].normals
		self.vertices = scene.meshes[mesh_index].vertices
		self.x = x
		self.y = y
		self.z = z
		self.size = scale

	def move(x, y, z):
		self.x += x
		self.y += y
		self.z += z




# Initialization of Window
width, height = 1280, 720
pygame.init()
window = pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
pygame.display.set_caption("Hololo")

# Testing and Importing Meshes With Assimp (https://www.assimp.org)
scene = pyassimp.load("Template/cube.stl")
test_mesh = Mesh(scene)


# Main Loop
running = True
while running:
	pygame.display.flip()
	pygame.time.wait(10)

pygame.quit()