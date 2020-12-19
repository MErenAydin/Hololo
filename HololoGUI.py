import pygame
from pygame.locals import *
import pyassimp
import moderngl
import numpy as np
import struct
from pyrr import Matrix44,Quaternion,Vector3, Vector4, aabb
import pygame_gui
from PIL import Image, ImageDraw, ImageChops

import tkinter as tk
from tkinter import filedialog as fd 
from tkinter import messagebox as mbox

root = tk.Tk()
root.withdraw()

width, height = 1280, 720

def grid(size, steps):
	u = np.repeat(np.linspace(-size, size, steps), 2)
	v = np.tile([-size, size], steps)
	w = np.zeros(steps * 2)
	return np.concatenate([np.dstack([u, v, w])[:][:][0], np.dstack([v, u, w])[:][:][0]])

class Transform:
	
	
	def __init__(self, pos = Vector3([0,0,0]), rot = Quaternion.from_matrix(Matrix44.identity()), scale = Vector3([1,1,1])):
		
		self.__model_mat = Matrix44.identity()
		
		self.__pos = list(pos)
		self.__rot = list(rot)
		self.__scale = scale
		self.__changed = True
		
	def get_transformation_matrix(self):
		if self.__changed:
			matrix = Matrix44.from_quaternion(self.rot)
			matrix *= Matrix44.from_scale(self.scale)
			self.__model_mat = matrix * Matrix44.from_translation(self.pos)
			self.__changed = False
		return self.__model_mat
		
		
		
	def get_pos(self):
		return self.__pos
		
	def set_pos(self, value):
		self.__pos = value
		self.__changed = True
		
	def get_rot(self):
		return self.__rot
		
	def set_rot(self, value):
		self.__rot = value
		self.__changed = True
		
	def get_scale(self):
		return self.__scale
		
	def set_scale(self, value):
		self.__scale = value
		self.__changed = True
		
	pos = property(get_pos, set_pos)
	rot = property(get_rot, set_rot)
	scale = property(get_scale, set_scale)
	
	def get_euler(self):
		return self.__rot.axis

class Mesh:
	def __init__(self, vertices, indices = None, normals = None):
		

		self.normals = normals if normals is not None else np.zeros((len(vertices),3))
		self.indices = indices if indices is not None else np.array(list(range(len(vertices))))
		
		vertices = np.append(vertices, self.normals,1)
		
		self.vertices = [j for i in vertices for j in i]
		
		# super().__init__(pos, rot, scale)
		# self.scene = scene
		# self.normals = scene.meshes[mesh_index].normals
		
		# self.vertices = scene.meshes[mesh_index].vertices
		# self.model_mat = Matrix44.from_translation(np.array(pos))
		
		# print(self.vertices)

		# vertices = np.append(self.vertices, self.normals,1)
		# self.min_z = vertices[:,2].min()
		# flatten = [j for i in vertices for j in i]

		# self.context = Shader(scale, flatten , pos)

	
	
	@staticmethod
	def from_assimp_mesh(mesh):
		normals = mesh.normals
		vertices = mesh.vertices
		
		# vertices = np.append(vertices, normals,1)
		
		# flatten = [j for i in vertices for j in i]
		return Mesh(vertices, normals = normals)
	
	@staticmethod
	def from_file(path, mesh_index = 0):
		scene = pyassimp.load(path)
		return Mesh.from_assimp_mesh(scene.meshes[mesh_index])
		
	def calculate_bounding_box(self):
		return aabb.from_points(self.vertices)

class Model:
	def __init__(self, mesh, transform = Transform(), color = (.7, .5, .3 , 1.0), v_shader_path = "Shaders/model_v.shader" , f_shader_path = "Shaders/model_f.shader"):
		
		
		self.transform = transform
		self.mesh = mesh
		
		self.program = context.program(
			vertex_shader = open(v_shader_path).read(),
			fragment_shader = open(f_shader_path).read(),
			)
			
		self.color = color
		
		self._model = self.program['model']
		self._view = self.program['view']
		self._projection = self.program['projection']
		self._color = self.program['objectColor']
		self._light_pos = self.program['lightPos']
		self._light_color = self.program['lightColor']
		
		self.vbo = context.buffer(struct.pack("{0:d}f".format(len(self.mesh.vertices)), *self.mesh.vertices))
		# self.vbo = context.buffer(self.mesh.vertices.astype("f4"))
		#self.ebo = context.buffer(self.mesh.indices.astype("uint32").tobytes())
		self.vao = context.simple_vertex_array(self.program, self.vbo, 'aPos','aNormal')
		
	def render(self, camera,  light, render_type = moderngl.TRIANGLES):
	
		self._projection.write(camera.projection.astype('float32').tobytes())
		self._view.write(camera.get_view_matrix().astype('float32').tobytes())
		self._model.write(self.transform.get_transformation_matrix().astype('float32').tobytes())
		self._color.value = self.color
		self._light_color.value = light.color
		self._light_pos.value = tuple(light.pos)

		self.vao.render(render_type)
	
	def reload(self):
		self.vbo.write(struct.pack("{0:d}f".format(len(self.mesh.vertices)), *self.mesh.vertices))

class Camera:
	def __init__(self, pos, look_point, up = Vector3([0.0, 0.0, 1.0])):
	
		self._init_pos = pos
		self.pos = pos
		self.rot = [np.arctan2(np.sqrt(self.pos[2] ** 2 + self.pos[0] ** 2), self.pos[1]),
					np.arctan2(np.sqrt(self.pos[0] ** 2 + self.pos[1] ** 2), self.pos[2]),
					np.arctan2(np.sqrt(self.pos[1] ** 2 + self.pos[2] ** 2), self.pos[0])]
		self.up = up
		self.radius = np.sqrt((pos[0] - look_point[0]) ** 2 + (pos[1] - look_point[1]) ** 2 + (pos[2] - look_point[2]) ** 2)
		self.look_point = look_point
		
		self.view = Matrix44.look_at(pos, look_point, up)
		self.projection = Matrix44.perspective_projection(45.0, width / height, 0.1, 1000.0)
		
		self.__changed = True
	
	def get_view_matrix(self):
		if self.__changed:
			self.view = Matrix44.look_at(self.pos, self.look_point, self.up)
			self.__changed = False
		return self.view
		
	def rotate(self, rotation_vector):
		self.rot = [a+b for a, b in zip(self.rot, [x / 250.0 for x in rotation_vector])]
		self.rot[1] = np.clip(self.rot[1], 0.1, np.pi - 0.1)
		
		self.pos = [np.sin(self.rot[1]) * np.cos(self.rot[2]), np.sin(self.rot[1]) * np.sin(self.rot[2]) , np.cos(self.rot[1])]
		self.pos = [a* self.radius for a in self.pos]
		
		self.__changed = True
 	
	def distance(self, raw_scroll):
		delta = 0.9
		if raw_scroll > 0:
			self.radius *= delta
		elif raw_scroll < 0:
			self.radius /= delta
			
		self.radius = np.clip(self.radius, 3, 50)
		self.pos = [np.sin(self.rot[1]) * np.cos(self.rot[2]), np.sin(self.rot[1]) * np.sin(self.rot[2]) , np.cos(self.rot[1])]
		self.pos = [a* self.radius for a in self.pos]
		self.__changed = True
	
	def reset(self):
		self.pos = self._init_pos
		self.rot = [np.arctan2(np.sqrt(self.pos[2] ** 2 + self.pos[0] ** 2), self.pos[1]),
					np.arctan2(np.sqrt(self.pos[0] ** 2 + self.pos[1] ** 2), self.pos[2]),
					np.arctan2(np.sqrt(self.pos[1] ** 2 + self.pos[2] ** 2), self.pos[0])]
		self.radius =  np.sqrt((self.pos[0] - self.look_point[0]) ** 2 + (self.pos[1] - self.look_point[1]) ** 2 + (self.pos[2] - self.look_point[2]) ** 2)
		self.__changed = True

class Light:
	def __init__(self, pos, color = (1.0, 1.0, 1.0)):
		self.pos = pos
		self.color = color

class Gizmo(Transform):
	def __init__(self, pos = (0.0, 0.0, 0.0), rot = (0.0, 0.0, 0.0), scale = 1, mesh = None, type = "", v_shader_path = "Shaders/model_v.shader", f_shader_path = "Shaders/model_f.shader"):
		super().__init__(pos, rot, scale)
		
		if type == "rot":
			scene = pyassimp.load("Template/rotate_gizmo.stl")
		elif type == "scale":
			scene = pyassimp.load("Template/scale_gizmo.stl")
		else:
			scene = pyassimp.load("Template/move_gizmo.stl")
		
		self.normals = scene.meshes[0].normals
		self.vertices = scene.meshes[0].vertices
		self.model_mat = Matrix44.from_translation(np.array(pos))
		
		vertices = np.append(self.vertices, self.normals,1)
		
		flatten = [j for i in vertices for j in i]
		if mesh:
			self.context = Shader(scale, flatten, mesh.pos)
		else:
			self.context = Shader(scale, flatten, self.pos)
	def render(self):
		color = (0, 0 , 255 , 255) 
		proj = Matrix44.perspective_projection(45.0, width / height, 0.1, 1000.0)
		
		context.screen.color_mask = False, False, False, False
		context.clear(depth=1.0, viewport = (width, height))
		context.screen.color_mask = True, True, True, True
		
		self.context._scale.value = 1.0
		self.context._projection.write(proj.astype('float32').tobytes())
		self.context._view.write(camera.look_at.astype('float32').tobytes())
		
		self.context._rotation.write(rotate.astype('float32').tobytes())
		self.model_mat = Matrix44.identity()
		self.context._model.write(self.model_mat.astype('float32').tobytes())
		self.context._color.value = color
		self.context.vao.render(moderngl.TRIANGLES)
		
		self.rotate(np.pi /2,0,0)
		self.context._color.value = (0,255,0,255)
		self.context.vao.render(moderngl.TRIANGLES)
		
		self.rotate(0,-np.pi /2,0)
		self.context._color.value = (255,0,0,255)
		self.context.vao.render(moderngl.TRIANGLES)	
	
	def rotate(self, x, y, z):
		super().rotate((x,y,z))
		matrix = Matrix44.from_x_rotation(x)
		matrix *= Matrix44.from_y_rotation(y)
		matrix *= Matrix44.from_z_rotation(z)
		self.model_mat = matrix
		self.context._model.write(self.model_mat.astype('float32').tobytes())
	
	def rotate_relative(self, x, y, z):
		super().rotate((x,y,z))
		matrix = Matrix44.from_x_rotation(x)
		matrix *= Matrix44.from_y_rotation(y)
		matrix *= Matrix44.from_z_rotation(z)
		self.model_mat *= matrix
		self.context._model.write(self.model_mat.astype('float32').tobytes())

class Viewport:
	
	def __init__(self, manager, v_shader_path = "Shaders/texture_v.shader", f_shader_path = "Shaders/texture_f.shader"):
		
		self.__image = Image.new("RGBA", (width, height), (0,0,0,0))
		self.manager = manager
		
		vertices = np.array([
			0.0, 0.0, 0.0, 1.0,
			width, 0.0, 1.0, 1.0,
			0.0, height, 0.0, 0.0,
			0.0, height, 0.0, 0.0,
			width, 0.0, 1.0, 1.0,
			width, height, 1.0 ,0.0
		])
		
		self.program = context.program( 
			vertex_shader = open(v_shader_path).read(),
			fragment_shader = open(f_shader_path).read(),
			)
			
		#self.program['RenderMode'].value = moderngl.TEXTURE_MODE
		
		self.texture = context.texture(self.image.size, 4, self.image.tobytes())
		
		self.texture.use(0)
		
		self.w_size = self.program["w_size"]
		self.w_size.write(np.array([width,height]).astype('f4').tobytes())
		
		self.vbo = context.buffer(vertices.astype('f4').tobytes())
		self.vao = context.simple_vertex_array(self.program, self.vbo, 'in_vert', 'in_text')
		
	def add_image(self, img, pos):
		temp = self.image.copy()
		temp.paste(img, pos)
		self.image = temp
		
	def get_image(self):	
		return self.__image
		
	def set_image(self, value):
		diff = ImageChops.difference(self.__image.copy().convert("RGB"), value.copy().convert("RGB"))
		
		if diff.getbbox():
			self.__image = value
			self.texture.write(self.__image.tobytes())
			self.texture.use(0)
		
	def get_concat_h(self, im1, im2):
		dst = Image.new('RGBA', (im1.width + im2.width, im1.height))
		dst.paste(im1, (0, 0))
		dst.paste(im2, (im1.width, 0))
		return dst
		
	
	image = property(get_image, set_image)
	
	def render(self):
		self.vao.render(moderngl.TRIANGLES)
		
class Button:

	def __init__(self, rect_pos, rect_size, button_name, button_text, viewport, handler = None, image_path = None, text_color = (0, 0, 0) , bg_color = (220, 220, 220, 255), o_width = 5 , three_D = True):
		
		self.__hover = False
		self.__clicked = False
		
		self.rect_pos = rect_pos
		self.rect_size = rect_size
		self.button_name = button_name
		self.button_text = button_text
		self.viewport = viewport
		self.image_path = image_path
		self.text_color = text_color
		self.bg_color = bg_color
		self.width = o_width
		self.three_D = three_D
		self.handler = handler
		
		viewport.manager.buttons[button_name] = self
		
		viewport.add_image(self.get_image(self.bg_color, self.text_color), self.rect_pos)
		
	def get_image(self, bg_color , text_color, clicked = False):
		if self.image_path != None:
			button_image = Image.open(self.image_path, "RGBA")
		else:
			button_image = Image.new("RGBA", self.rect_size, bg_color)
			draw = ImageDraw.Draw(button_image)
			if self.three_D:
				lc = [a + 30 for a in bg_color[0:3]]
				lc.append(bg_color[3])
				dc = [a - 30 for a in bg_color[0:3]]
				dc.append(bg_color[3])
				if clicked:
					temp = lc
					lc = dc
					dc = temp
				f = list(bg_color[0:3])
				f.append(bg_color[3])
				
				draw.rectangle(((0, 0),(button_image.size[0] - 1, button_image.size[1] - 1)), fill = tuple(f), outline = tuple(dc), width = self.width)
				draw.polygon(((0,0), (0,button_image.size[1] - 1), (self.width - 1, button_image.size[1] - self.width  ), (self.width - 1, self.width - 1), (button_image.size[0] - self.width, self.width - 1 ),(button_image.size[0] - 1, 0)), fill = tuple(lc))
					
			
			else:
				draw.rectangle(((self.width // 2 - 1, self.width // 2 - 1), (self.rect_size[0] - (self.width // 2), self.rect_size[1] - (self.width // 2))), fill= self.bg_color, outline = (0,0,0,255), width = self.width)
			
			button_image = button_image.resize(self.rect_size)
			
		img = font.render(self.button_text, True, text_color)
		string_image = pygame.image.tostring(img, "RGBA", False)
		img = Image.frombytes("RGBA", img.get_size(), string_image)
		# wpercent = (self.prefered_height/float(img.size[0]))
		# hsize = int((float(img.size[1])*float(wpercent)))
		# img = img.resize((self.prefered_height,hsize), Image.ANTIALIAS)
		
		offset = (self.rect_size[0] // 2 - (img.size[0] // 2), self.rect_size[1] // 2 - (img.size[1] // 2))
		button_image.paste(img, offset, img)
		
		return button_image
		
	def get_hover(self):
		return self.__hover
		
	def set_hover(self, value):
		changed = self.hover != value
		self.__hover = value
		if changed:
			if value:
				if not self.__clicked:
					hover_color = []
					for i in range(len(self.bg_color) - 1):
						
						if (self.bg_color[i] + 20 <= 255):
							hover_color.append(self.bg_color[i] + 20)
						else:
							hover_color.append(self.bg_color[i])
						
					hover_color.append(self.bg_color[-1])
					hover_color = tuple(hover_color)
					img = self.get_image(hover_color, self.text_color)
					viewport.add_image(img, self.rect_pos)
				
			else:
				img = self.get_image(self.bg_color, self.text_color)
				viewport.add_image(img, self.rect_pos)
		
	hover = property(get_hover, set_hover)
	
	def get_clicked(self):
		return self.__clicked
	
	def set_clicked(self, value):
		self.__clicked = value
		if value:
			if self.__hover:
				click_color = []
				if self.handler:
					self.handler()
				for i in range(len(self.bg_color) - 1):
					if (self.bg_color[i] - 20 >= 0):
						click_color.append(self.bg_color[i] - 20)
					else:
						click_color.append(self.bg_color[i])
				
				
				click_color.append(self.bg_color[-1])
				click_color = tuple(click_color)
				img = self.get_image(click_color, self.text_color, clicked = True)
				viewport.add_image(img, self.rect_pos)
				return
			else:
				self.__clicked = False
				img = self.get_image(self.bg_color, self.text_color)
				viewport.add_image(img, self.rect_pos)
		else:
			img = self.get_image(self.bg_color, self.text_color)
			viewport.add_image(img, self.rect_pos)
		
	clicked = property(get_clicked, set_clicked)

class Manager:
	def __init__(self):
		self.buttons = {}
		
	def update(self, event):
		if (event.type == MOUSEMOTION):
			pos = event.pos
			rel = event.rel
			buttons = event.buttons
			
			self.is_collides_buttons(pos)
			
		if (event.type == MOUSEBUTTONDOWN):
			button = event.button
			if button == 1:
				for button_name in self.buttons:
					clicked_button = self.buttons[button_name]
					clicked_button.clicked = True
						
		if (event.type == MOUSEBUTTONUP):
			button = event.button
			if button == 1:
				for button_name in self.buttons:
					clicked_button = self.buttons[button_name]
					if clicked_button.clicked:
						clicked_button.clicked = False

	def is_collides_buttons(self, point):
		for button_name in self.buttons:
					
			button = self.buttons[button_name]
			if (point[0] >=  button.rect_pos[0] and point[0] <= button.rect_pos[0]  + button.rect_size[0] ) and (point[1] >= button.rect_pos[1] and point[1] <= button.rect_pos[1]  + button.rect_size[1]):
				button.hover = True
				
			else:
				button.hover = False

"""# class TextInput():
	# def __init__(self, rect_pos, rect_size, viewport, text = "", image_path = None, text_color = (0, 0, 0) , bg_color = (255, 255, 255, 255), o_width = 2):
		# self.text_color = text_color
		# self.__text = " "
		# self.rect_size = rect_size
		# self.rect_pos = rect_pos
		# self.bg_color = bg_color
		# self.width = o_width
		# self.image_path = image_path
		
		# if image_path != None:
			# self.text_input_image = Image.open(image_path, "RGBA")
		# else:
			# self.text_input_image = Image.new("RGBA", rect_size, bg_color)
			# draw = ImageDraw.Draw(self.text_input_image)
			# draw.rectangle(((o_width // 2 - 1, o_width // 2 - 1), (rect_size[0] - (o_width // 2), rect_size[1] - (o_width // 2))), fill= bg_color, outline = (0,0,0,255), width = o_width)
			# self.text_input_image = self.text_input_image.resize(rect_size)
		
		# viewport.add_image(self.text_input_image, rect_pos)
		
	# def clear(self):
		# if self.image_path != None:
			# self.text_input_image = Image.open(self.image_path, "RGBA")
		# else:
			# self.text_input_image = Image.new("RGBA", self.rect_size, self.bg_color)
			# draw = ImageDraw.Draw(self.text_input_image)
			# draw.rectangle(((self.width // 2 - 1, self.width // 2 - 1), (self.rect_size[0] - (self.width // 2), self.rect_size[1] - (self.width // 2))), fill= self.bg_color, outline = (0,0,0,255), width = self.width)
			# self.text_input_image = self.text_input_image.resize(self.rect_size)
	
	# def set_text(self, value):
		# self.__text = value
		
		# self.clear()
		
		# img = font.render(self.__text, True, self.text_color)
		# string_image = pygame.image.tostring(img, "RGBA", False)
		# img = Image.frombytes("RGBA", img.get_size(), string_image)
		
		# h = self.rect_size[1] -2 * self.width
		# aspect = img.size[0] / (3 * h)
		# w = int(img.size[1] * aspect)
		# img = img.resize((w,h), Image.ANTIALIAS)
		
		# offset = (self.width, self.rect_size[1] // 2 - (img.size[1] // 2))
		# if w >= self.text_input_image.size[0] - 20:
			# img = img.crop((img.size[0] - self.text_input_image.size[0] + (2 * self.width), 0, img.size[0], img.size[1]))
		# self.text_input_image.paste(img, offset, img)
		
		# viewport.add_image(self.text_input_image, self.rect_pos)
		
		
	# def get_text(self):
		# return self.__text
		
	# text = property(get_text, set_text)
"""

						
					
def render():
	print("Render")
	
def app_quit():
	global running 
	running = False
	
def load():
	names = fd.askopenfilenames()
	for i, name in enumerate(names):
		try:
			mesh_list.append(Model(Mesh.from_file(name), color = (.7, .5, i * .1 , 1.0)))
		except Exception as e:
			print(e)
		except:
			mbox.showerror("Load Error" , "Could not load " + name)
# Initialization of Window


pygame.init()

pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)

#[print(a) for a in sorted(pygame.font.get_fonts())]

#font = pygame.font.SysFont("OpenSans-Light.ttf", 50)
font = pygame.font.Font("Font\OpenSans-Regular.ttf", 16)
# img = font.render('The quick brown fox jumps over the lazy dog', True, (0,0,255))

# string_image = pygame.image.tostring(img, "RGBA", False)
# img = Image.frombytes("RGBA", img.get_size(), string_image)



window = pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
pygame.display.set_caption("Hololo")


context = moderngl.create_context(require=330)
context.enable(moderngl.DEPTH_TEST)
context.enable(moderngl.BLEND)
context.enable(moderngl.CULL_FACE)
context.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)
# fbo = context.simple_framebuffer((width,height))
# fbo.use()
#texture = Texture((0,0), img)

manager = Manager()

viewport = Viewport(manager)

btn = Button((20,height - 40 -80), (100, 40), "Render", "Render", viewport, handler = render)

btn2 = Button((20,height - 40 - 20), (100, 40), "Quit", "Quit", viewport, handler = app_quit)

btn3 = Button((20,height - 40 - 140), (100, 40), "Load", "Load", viewport, handler = load)

# Testing and Importing Meshes With Assimp (https://www.assimp.org)
mesh_list = []

#scene = pyassimp.load("Template/display_area.stl")
#mesh_list.append(Mesh(scene, pos = (0.0,0.0,0.0)))

#gizmo = Gizmo()

grid = Model(Mesh(grid(5.0,11)), color = (0,0,0,1))

mesh_list.append(Model(Mesh.from_file("Template/display_area.stl"), color = (0, 1, 0, 0.25)))



init_camera_pos = Vector3([10.0, 0.0, 2.5])
origin = (0.0,0.0,0.0)
camera = Camera(init_camera_pos, origin)

light = Light(init_camera_pos)
# Main Loop

clock = pygame.time.Clock()

running = True

while running:
	
	time_delta = clock.tick(60)/1000.0
	
	
	for event in pygame.event.get():
	
		manager.update(event)
		if event.type == pygame.QUIT:
			running = False
			
		elif (event.type == MOUSEBUTTONDOWN):

			pos = event.pos
			button = event.button
			
			
			if button == 1:
				x = ((pos[0]) / (width)) *2 -1;
				y = ((pos[1]) / (height)) * 2 -1;
				z = 0;
				w = 1;
				
				
				pv = camera.projection * camera.get_view_matrix()
				
				t = pv.inverse * Vector4((x,y,z,w))
				transform = np.array((t.x / t.w, t.y / t.w, t.z / t.w))
				cam_pos = np.array(camera.pos)
				
				ray = (transform - cam_pos)
				
				
			
		
		elif event.type == KEYDOWN:
			key = event.key
			if key == K_r:
				rotate = Matrix44.identity()
				camera.reset()
				rot_y = -0.25
				
			if key == K_LEFT:
				turn_left = True
			if key == K_RIGHT:
				turn_right = True
			

		elif event.type == MOUSEMOTION:

			pos = event.pos
			delta = event.rel
			buttons = event.buttons
			mul = 1
			mod = pygame.key.get_mods()

			# If pressed left or right shift transform more sensitive
			if mod & 2 or mod & 1:
				mul = 5

			# If mouse left clicked
			if buttons[0] == 1:
				if abs(delta[0]) <= width - 100 and abs(delta[1]) <= height - 100:
					camera.rotate([0, -delta[1], -delta[0]])
						

					# Do not let the mouse pointer go out of boundaries while transforming 
					if pos[0] >= width - 50:
						pygame.mouse.set_pos([55,pos[1]])
					elif pos[0] <= 50:
						pygame.mouse.set_pos([width - 55,pos[1]])
					if pos[1] >= height - 50:
						pygame.mouse.set_pos([pos[0],55])
					elif pos[1] <= 50:
						pygame.mouse.set_pos([pos[0],height - 55])
					
					light.pos = camera.pos
					
					# Clear the event buffer
					pygame.event.clear()

		# If mouse scroll moved
		elif event.type == MOUSEWHEEL:
				
			camera.distance(event.y)
	
	
	context.viewport = (0, 0, width, height)
	context.clear(0.7, 0.7, 0.9)
	grid.render(camera, light, render_type = moderngl.LINES)
	
	for mesh in mesh_list[1:]:
		mesh.render(camera, light, render_type = moderngl.TRIANGLES)
		#mesh.lean_floor()
	
	mesh_list[0].render(camera, light, render_type = moderngl.TRIANGLES)
	
	#gizmo.render()
	
	
	viewport.render()
	pygame.display.flip()
	pygame.time.wait(10)

	



pygame.quit()