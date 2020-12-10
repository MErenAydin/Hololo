import pygame
from pygame.locals import *
import pyassimp
import moderngl
import numpy as np
import struct
from pyrr import Matrix44,Quaternion,Vector3

class Mesh:
	def __init__(self, scene, x = 0, y = 0, z = 0, scale = 1, mesh_index = 0, v_shader_path = "Shaders/model_v.shader" , f_shader_path = "Shaders/model_f.shader"):
		self.scene = scene
		self.normals = scene.meshes[mesh_index].normals
		self.vertices = scene.meshes[mesh_index].vertices
		self.x = x
		self.y = y
		self.z = z
		self.size = scale
		self.context = moderngl.create_context()
		self.program = self.context.program(
			vertex_shader = open(v_shader_path).read(),
			fragment_shader = open(f_shader_path).read(),
			)
		self.vbo = bytearray()
		self.vao = bytearray()

		# Uniform 4x4 Matrices variables
		self._model = prog['model']
		self._view = prog['view']
		self._projection = prog['projection']
		self._rotation = prog['rotation']

		# Uniform Vector 3 variables
		self._light_pos = prog['lightPos']
		self._light_color = prog['lightColor']
		self._color = prog['objectColor']

		# Uniform Float Variable
		self._scale = prog['scale']


	def move(self, x, y, z):
		self.x += x
		self.y += y
		self.z += z
		model_mat = Matrix44.from_translation(np.array([self.y,self.x,self.z]))
		self._model.write(model_mat.astype('float32').tobytes())

	def init_mesh(self, light_pos = (0,0,0), light_color = (1,1,1), ):
		self._light_pos.value = light_pos
		self._light_color = light_color

		model_mat = Matrix44.from_translation(np.array([self.y,self.x,self.z]))
		self._model.write(model_mat.astype('float32').tobytes())

		vertices = np.append(self.vertices, self.normals,1)
		flatten = [j for i in vertices for j in i]

		self.vbo = self.context.buffer(struct.pack("{0:d}f".format(len(flatten)),*flatten))
		self.vao = self.context.simple_vertex_array(self.program, self.vbo, 'aPos','aNormal')

	def render(self):
		pass





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