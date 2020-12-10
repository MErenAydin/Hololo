import pygame
from pygame.locals import *
import pyassimp
import moderngl
import numpy as np
import struct
from pyrr import Matrix44,Quaternion,Vector3

class Mesh:
	def __init__(self, scene, pos = (0,0,0), rot = (0,0,0), scale = 1, mesh_index = 0):
		self.scene = scene
		self.normals = scene.meshes[mesh_index].normals
		self.vertices = scene.meshes[mesh_index].vertices

		self.transform = Transform(pos, rot, scale)

		vertices = np.append(self.vertices, self.normals,1)
		flatten = [j for i in vertices for j in i]

		self.context = Context(scale, flatten)


	def move(self, x, y, z):
		self.transform.pos += (x,y,z)
		model_mat = Matrix44.from_translation(np.array([x,y,z]))
		self._model.write(model_mat.astype('float32').tobytes())

	def rotate(self, x, y, z):
		self.transform.rot += (x,y,z)
		model_mat = Matrix44.from_euler(np.array([x,y,z]))
		#model_mat = Matrix44.from_translation(np.array([x,y,z]))
		self._model.write(model_mat.astype('float32').tobytes())

	def render(self):
		proj = Matrix44.perspective_projection(45.0, width / height, 0.1, 1000.0)
		self.context._projection.write(proj.astype('float32').tobytes())


		self.context._view.write(look_at.astype('float32').tobytes())


		self.context._rotation.write(rotate.astype('float32').tobytes())

		self.context.context.viewport = (0, 0, width, height)
		self.context.context.clear(0.7, 0.7, 0.9)

		self.context._color.value = (0.67, 0.49, 0.29 , 1.0)
		self.context.vao.render(moderngl.TRIANGLES)

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

		self._scale.write(struct.pack("f",scale))

		self.vbo = self.context.buffer(struct.pack("{0:d}f".format(len(flatten)),*flatten))
		self.vao = self.context.simple_vertex_array(self.program, self.vbo, 'aPos','aNormal')

		self.context.enable(moderngl.DEPTH_TEST)
		self.context.enable(moderngl.BLEND)
		self.context.enable(moderngl.CULL_FACE)
		self.context.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)
		
class Transform:
	def __init__(self, pos, rot, scale):
		self.pos = pos
		self.rot = rot
		self.scale = scale




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
rot_y = -0.25
rot_z = 0
s = 1.0

running = True
while running:

	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			running = False
		elif event.type == KEYDOWN:
			key = event.key
			if key == K_r:
				rotate = Matrix44.identity()
				look_at = init_look.copy()
				rot_y = -0.25

		elif event.type == MOUSEMOTION:

			pos = event.pos
			delta = event.rel
			buttons = event.buttons
			mul = 1
			mod = pygame.key.get_mods()
			if mod & 2 or mod & 1:
				mul = 5

			if buttons[0] == 1:
				if abs(delta[0]) <= width - 100 and abs(delta[1]) <= height - 100:
					rotate *= Matrix44.from_z_rotation(-delta[0]/(250.0 * mul))
					rot_z += -delta[0]/(250.0 * mul)
					rot_y += -delta[1]/(250.0 * mul)


					if rot_y > -np.pi /2 and rot_y < np.pi / 2:
						look_at *= Matrix44.from_y_rotation(-delta[1]/(250.0 * mul))
					else:
						rot_y = np.clip(rot_y, -np.pi / 2 , np.pi / 2)

					#light_mat = rotate * 0.0001
					#light_pos = light_mat * light_pos

					if pos[0] >= width - 30:
						pygame.mouse.set_pos([35,pos[1]])
					elif pos[0] <= 30:
						pygame.mouse.set_pos([width - 35,pos[1]])
					if pos[1] >= height - 30:
						pygame.mouse.set_pos([pos[0],35])
					elif pos[1] <= 30:
						pygame.mouse.set_pos([pos[0],height - 35])

					pygame.event.clear()

		elif event.type == MOUSEWHEEL:
			s += event.y / (30.0 * mul)
			if s < 0.02:
				s = 0.02
			test_mesh.context._scale.write(struct.pack("f",s))


	test_mesh.render()

	pygame.display.flip()
	pygame.time.wait(10)

	

pygame.quit()