import pygame
from pygame.locals import *
import pyassimp
import moderngl
import numpy as np
import struct
from pyrr import Matrix44,Quaternion,Vector3

class Mesh:
	def __init__(self, scene, x = 0, y = 0, z = 0, scale = 1, mesh_index = 0):
		self.scene = scene
		self.normals = scene.meshes[mesh_index].normals
		self.vertices = scene.meshes[mesh_index].vertices
		self.x = x
		self.y = y
		self.z = z
		self.scale = scale

		vertices = np.append(self.vertices, self.normals,1)
		flatten = [j for i in vertices for j in i]

		self.context = Context(self.scale, flatten)


	def move(self, x, y, z):
		self.x += x
		self.y += y
		self.z += z
		model_mat = Matrix44.from_translation(np.array([self.y,self.x,self.z]))
		self._model.write(model_mat.astype('float32').tobytes())

	def render(self):
		pass

class Context:
	def __init__(self, scale, flatten, pos = (0,0,0), light_pos = (0,0,0), light_color = (1,1,1), v_shader_path = "Shaders/model_v.shader" , f_shader_path = "Shaders/model_f.shader"):
		self.context = moderngl.create_context()
		self.program = self.context.program(
			vertex_shader = open(v_shader_path).read(),
			fragment_shader = open(f_shader_path).read(),
			)

		# Uniform 4x4 Matrices variables
		self._model = self.program['model']
		self._view = self.program['view']
		self._projection = self.program['projection']
		self._rotation = self.program['rotation']

		# Uniform Vector 3 variables
		self._light_pos = self.program['lightPos']
		self._light_color = self.program['lightColor']
		self._color = self.program['objectColor']

		# Uniform Float Variable
		self._scale = self.program['scale']



		self._light_pos.value = light_pos
		self._light_color.value = light_color

		model_mat = Matrix44.from_translation(np.array([pos[0],pos[1],pos[2]]))
		self._model.write(model_mat.astype('float32').tobytes())

		#vertices = np.append(self.vertices, self.normals,1)
		#flatten = [j for i in vertices for j in i]

		self._scale.write(struct.pack("f",scale))

		self.vbo = self.context.buffer(struct.pack("{0:d}f".format(len(flatten)),*flatten))
		self.vao = self.context.simple_vertex_array(self.program, self.vbo, 'aPos','aNormal')

		self.context.enable(moderngl.DEPTH_TEST)
		self.context.enable(moderngl.BLEND)
		self.context.enable(moderngl.CULL_FACE)
		self.context.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)
		




# Initialization of Window
width, height = 1280, 720
pygame.init()
window = pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
pygame.display.set_caption("Hololo")

# Testing and Importing Meshes With Assimp (https://www.assimp.org)
scene = pyassimp.load("Template/cube.stl")
test_mesh = Mesh(scene)


# Main Loop

init_look = Matrix44.look_at(
        (10, 0.0, 2.5),
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 1.0),
)
look_at = init_look.copy()
rotate = Matrix44.identity()

running = True
while running:

	proj = Matrix44.perspective_projection(45.0, width / height, 0.1, 1000.0)
	test_mesh.context._projection.write(proj.astype('float32').tobytes())


	test_mesh.context._view.write(look_at.astype('float32').tobytes())


	test_mesh.context._rotation.write(rotate.astype('float32').tobytes())

	test_mesh.context.context.viewport = (0, 0, width, height)
	test_mesh.context.context.clear(0.7, 0.7, 0.9)

	test_mesh.context._color.value = (0.67, 0.49, 0.29 , 1.0)
	test_mesh.context.vao.render(moderngl.TRIANGLES)

	pygame.display.flip()
	pygame.time.wait(10)

	

pygame.quit()