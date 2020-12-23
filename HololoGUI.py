
"""
	TODO:
		- Multiple object selection
		- Rotating and scaling with gizmo (and snapping with keyboard)
		- Text input for actions
		- Fix unselection of mesh while selecting transformation mode from screen
		- Implement quaternion to euler
		- Scaling gizmo with it's distance of camera 
		
		- Make classes seperate documents
"""

import pygame
from pygame.locals import *
import pyassimp
import moderngl
import numpy as np
import struct
from pyrr import Matrix44,Quaternion,Vector3, Vector4, aabb
import pyrr
import pygame_gui
from PIL import Image, ImageDraw, ImageChops, ImageOps, ImageFilter, ImageEnhance

import tkinter as tk
from tkinter import filedialog as fd 
from tkinter import messagebox as mbox
import os
import copy

root = tk.Tk()
root.withdraw()

width, height = 1280, 720

def grid(size, steps):
	# Returns numpy array of vertices of square grid which has given size and steps
	u = np.repeat(np.linspace(-size, size, steps), 2)
	v = np.tile([-size, size], steps)
	w = np.zeros(steps * 2)
	return np.concatenate([np.dstack([u, v, w])[:][:][0], np.dstack([v, u, w])[:][:][0]])

class Transform:
	def __init__(self, pos = None, rot = None, scale = None):
		
		self.__model_mat = Matrix44.identity()
		
		self.__pos = pos if pos is not None else Vector3([0.0,0.0,0.0])
		self.__rot = rot if rot is not None else Quaternion.from_matrix(Matrix44.identity())
		self.__scale = scale if scale is not None else Vector3([1.0,1.0,1.0])
		# Variable for reducing calculation of transformation matrix by checking if any variable changed
		self.__changed = True
		self.get_transformation_matrix()
		
	def __str__(self):
		return "Position: {}\nRotation: {}\nScale: {}".format(self.pos,self.rot,self.scale)
		
	def get_transformation_matrix(self):
		if self.__changed:
			matrix = Matrix44.from_translation(self.pos)
			matrix *= Matrix44.from_scale(self.scale)
			self.__model_mat = matrix * Matrix44.from_quaternion(self.rot)
			
			self.__changed = False
		return self.__model_mat
		
	# Getters and setters for properties
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
		
	# Properties
	pos = property(get_pos, set_pos)
	rot = property(get_rot, set_rot)
	scale = property(get_scale, set_scale)
	
	# TODO: Will be implemented
	def get_euler(self):
		return self.__rot.axis
	
	# Returns copy of instance
	def copy(self):
		return Transform(self.pos.copy(), self.rot.copy(), self.scale.copy())
	
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
	def __init__(self, mesh, transform = None, color = (.7, .5, .3 , 1.0), v_shader_path = "Shaders/model_v.shader" , f_shader_path = "Shaders/model_f.shader"):
		
		
		self.transform = transform if transform is not None else Transform()
		self.mesh = mesh
		
		self.v_shader_path = v_shader_path
		self.f_shader_path = f_shader_path
		
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
		self._selection = self.program['selection']
		self._grow = self.program['grow']
		
		self.vbo = context.buffer(struct.pack("{0:d}f".format(len(self.mesh.vertices)), *self.mesh.vertices))
		# self.vbo = context.buffer(self.mesh.vertices.astype("f4"))
		#self.ebo = context.buffer(self.mesh.indices.astype("uint32").tobytes())
		self.vao = context.simple_vertex_array(self.program, self.vbo, 'aPos','aNormal')
		
	def render(self, camera,  light, render_type = moderngl.TRIANGLES, selection = False , selected = False):
		
		self._projection.write(camera.projection.astype('float32').tobytes())
		self._view.write(camera.get_view_matrix().astype('float32').tobytes())
		self._model.write(self.transform.get_transformation_matrix().astype('float32').tobytes())
		self._grow.value = 0.0 if selection else 0.0 
		self._color.value = self.color if not selected else tuple([i + 0.2 for i in self.color])
		self._light_color.value = light.color
		self._light_pos.value = tuple(light.pos)
		self._selection.value = selection
		self.vao.render(render_type)
	
	def reload(self):
		self.vbo.write(struct.pack("{0:d}f".format(len(self.mesh.vertices)), *self.mesh.vertices))

class Camera:
	def __init__(self, pos, look_point, up = None):
		
		self.up = up if up is not None else Vector3([0.0, 0.0, 1.0])
		self._init_pos = pos
		self.pos = pos
		[10, 0, 2.5]
		# self.rot = [np.arctan2(np.sqrt(self.pos[2] ** 2 + self.pos[0] ** 2), self.pos[1]),
					# np.arctan2(np.sqrt(self.pos[0] ** 2 + self.pos[1] ** 2), self.pos[2]),
					# np.arctan2(np.sqrt(self.pos[1] ** 2 + self.pos[2] ** 2), self.pos[0])]
		self.rot = [0,
					np.arctan2(np.sqrt(self.pos[0] ** 2 + self.pos[1] ** 2), self.pos[2]),
					0]
					
		self.radius = np.sqrt((pos[0] - look_point[0]) ** 2 + (pos[1] - look_point[1]) ** 2 + (pos[2] - look_point[2]) ** 2)
		self.look_point = look_point
		
		self.view = Matrix44.look_at(pos, look_point, self.up)
		self.projection = Matrix44.perspective_projection(45.0, width / height, 0.1, 1000.0)
		
		self.__changed = True
	
	def get_view_matrix(self):
		if self.__changed:
			self.view = Matrix44.look_at(list(self.pos), self.look_point, self.up)
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
		self.rot = [0,
					np.arctan2(np.sqrt(self.pos[0] ** 2 + self.pos[1] ** 2), self.pos[2]),
					0]
		self.radius =  np.sqrt((self.pos[0] - self.look_point[0]) ** 2 + (self.pos[1] - self.look_point[1]) ** 2 + (self.pos[2] - self.look_point[2]) ** 2)
		self.__changed = True
		
	def screen_to_world_coordinates(self,mouse_pos):
		x = ((mouse_pos[0]) / float(width)) * 2 -1;
		y = ((height - mouse_pos[1]) / float(height)) * 2 -1;
		z = 0.0;
		w = 1.0;
		
		
		pv = self.projection * self.get_view_matrix()
		
		t = pv.inverse * Vector4([x,y,z,w])
		return Vector3([t.x, t.y , t.z ]) / t.w
		
	def ray_cast(self, direction, plane, debug = False):
		ray = pyrr.ray.create(self.pos, direction)
		intersection = pyrr.geometric_tests.ray_intersect_plane(ray, plane)
		if debug:
			add_empty(debug_mesh_list, Transform(intersection))
		return intersection

class Light:
	def __init__(self, pos, color = (1.0, 1.0, 1.0)):
		self.pos = pos
		self.color = color

class Gizmo:
	def __init__(self, mode = "pos"):
		
		self.__transform = Transform()
		self.__mode = mode
		self.axis = None
		self.axis_t = None
		self.visible = False
		
		path = "Template/move_gizmo.stl"
			
		self.axis = Model(Mesh.from_file(path))
		path = os.path.splitext(path)
		self.axis_t = Model(Mesh.from_file(path[0] + "_t" + path[1]))

	def render(self, transform, camera,  light, render_type = moderngl.TRIANGLES, selection = False):
		
		scale = self.transform.scale.copy()
		self.transform = transform
		self.transform.pos = transform.pos.copy()
		self.transform.scale = scale
		
		if self.visible:
			context.screen.color_mask = False, False, False, False
			context.clear(depth= 1.0, viewport = (width, height))
			context.screen.color_mask = True, True, True, True
			
			temp = self.axis_t if selection else self.axis
			
			temp.transform = self.transform.copy()
			temp.transform.rot = Quaternion([0.0,0.0,0.0,1.0])
			temp.color = (0.0, 0.0, 1.0, 1.0) if selection else (0, 0, 255, 255)
			temp.render(camera, light, selection = selection)
			
			temp.transform.rot = Quaternion.from_y_rotation(-np.pi/2)
			temp.color = (0.0, 0.0, 1.0 / 3.0, 1.0) if selection else (255, 0, 0, 255)
			temp.render(camera, light, selection = selection)
			
			temp.transform.rot = Quaternion.from_x_rotation(np.pi/2)
			temp.color = (0.0, 0.0, 2.0 / 3.0, 1.0) if selection else (0, 255, 0, 255)
			temp.render(camera, light, selection = selection)
	
	def scale(self, scale_fac):
		self.transform.scale = np.clip(self.transform.scale.copy() * scale_fac, (0.9 ** 12), ((1.0 / 0.9) ** 15))
		# self.axis.transform.scale = self.transform.scale.copy()
		# self.axis_t.transform.scale = self.transform.scale.copy()
		
	
	def get_transform(self):
		return self.__transform
		
	def set_transform(self, value):
		self.__transform = value.copy()
		# self.axis.transform = value.copy()
		# self.axis_t.transform = value.copy()
		
	def get_mode(self):
		return self.__mode

	def set_mode(self, value):
		if self.__mode != value:
			if value == "rot":
				path = "Template/rotate_gizmo.stl"
			elif value == "scale":
				path = "Template/scale_gizmo.stl"
			else:
				path = "Template/move_gizmo.stl"
			
			self.axis = Model(Mesh.from_file(path), transform = self.transform.copy())
			path = os.path.splitext(path)
			self.axis_t = Model(Mesh.from_file(path[0] + "_t" + path[1]) ,transform = self.transform.copy())
			self.__mode = value
	
	mode = property(get_mode, set_mode)
	transform = property(get_transform, set_transform)

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

	def __init__(self, rect_pos, rect_size, button_name, viewport, button_text = "", handler = None, image_path = None, text_color = (0, 0, 0) , bg_color = (220, 220, 220, 255), o_width = 5 , three_D = False):
		
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
		
		self.image = self.get_image(self.bg_color, self.text_color) if self.image_path is None else self.get_image_from_file(self.image_path, self.rect_size)
		
		viewport.add_image(self.image, self.rect_pos)
		
	def get_image_from_file(self, path, size):
		button_image = Image.open(path)
		button_image = button_image.resize(size, Image.ANTIALIAS)
		
		return button_image
	
	def get_image(self, bg_color , text_color, clicked = False):
		
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
					enhancer = ImageEnhance.Brightness(self.image.copy())
					img = enhancer.enhance(1.1)
					viewport.add_image(img, self.rect_pos)
			else:
				viewport.add_image(self.image, self.rect_pos)
		
	hover = property(get_hover, set_hover)
	
	def get_clicked(self):
		return self.__clicked
	
	def set_clicked(self, value):
		self.__clicked = value
		if value:
			if self.__hover:
				if self.handler:
					self.handler()
					
				
				if self.three_D:
					img = self.get_image(self.bg_color, self.text_color, clicked = True)
				enhancer = ImageEnhance.Brightness(img if self.three_D else self.image.copy())
				img = enhancer.enhance(0.9)
				
				viewport.add_image(img, self.rect_pos)
			else:
				self.__clicked = False
				viewport.add_image(self.image, self.rect_pos)
		else:
			enhancer = ImageEnhance.Brightness(self.image.copy())
			img = enhancer.enhance(1.1)
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
			trns = Transform(pos = Vector3([0.0,0.0,0.0]))
			mesh_list.append(Model(Mesh.from_file(name), trns, color = (.7, .5, .1 , 1.0)))
		except Exception as e:
			print(e)
		except:
			mbox.showerror("Load Error" , "Could not load " + name)

def move():
	global gizmo
	gizmo.mode = "pos"
	
def rotate():
	global gizmo
	gizmo.mode = "rot"
	
def scale():
	global gizmo
	gizmo.mode = "scale"

def get_selected_mesh_index(model_list, camera, mouse_pos):
	global selected_index

	if len(model_list) == 0:
		return None, None
	context.clear(0.0, 0.0, 0.0, 1.0)
	
	for i,model in enumerate(model_list):
		temp = model.color
		model.color = ((1.0 / len(model_list)) * (i + 1), 0.0, 0.0, 1.0)
		model.render(camera, Light(Vector3([0.0,0.0,0.0])), selection = True)
		model.color= temp
	
	red = context.screen.read((mouse_pos[0], mouse_pos[1], 1, 1))[0]
	gizmo.render(model_list[selected_index].transform.copy() ,camera, Light(Vector3([0.0,0.0,0.0])), selection = True)
	blue = context.screen.read((mouse_pos[0], mouse_pos[1], 1, 1))[2]
	
	
	axis = int(blue * 3 / 255) - 1
	# ss = ImageOps.flip(Image.frombytes('RGB', (1280,720), context.screen.read((width, height))))
	# ss.show()
	
	red = red / 255.0
	index = int((red * len(model_list) - 1))
	
	if axis != -1:
		return selected_index, axis
	else:
		return index,axis

def add_empty(model_list, transform):
	model_list.append(Model(Mesh(np.array([[1.0,0.0,0.0],[-1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,-1.0,0.0],[0.0,0.0,1.0],[0.0,0.0,-1.0]])), transform.copy()))

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

btn = Button((20,height - 40 -80), (100, 40), "Render", viewport, "Render", handler = render, three_D = True)

btn2 = Button((20,height - 40 - 20), (100, 40), "Quit", viewport, "Quit", handler = app_quit, three_D = True)

btn3 = Button((20,height - 40 - 140), (100, 40), "Load", viewport, "Load", handler = load, three_D = True)

btn4 = Button((20,height - 40 - 250), (40,40), "Scale", viewport , image_path = "Textures/scale.png", handler = scale)

btn5 = Button((20,height - 40 - 310), (40,40), "Rotate", viewport , image_path = "Textures/rotate.png", handler = rotate)

btn6 = Button((20,height - 40 - 370), (40,40), "Move",  viewport , image_path = "Textures/move.png", handler = move)

# Testing and Importing Meshes With Assimp (https://www.assimp.org)
mesh_list = []
debug_mesh_list = []
#scene = pyassimp.load("Template/display_area.stl")
#mesh_list.append(Mesh(scene, pos = (0.0,0.0,0.0)))

gizmo = Gizmo()

grid = Model(Mesh(grid(5.0,11)), color = (0,0,0,1))

display_area = Model(Mesh.from_file("Template/display_area.stl"), color = (0, 1, 0, 0.25))

init_camera_pos = Vector3([10.0, 0.0, 2.5])
origin = (0.0,0.0,0.0)
camera = Camera(init_camera_pos, origin)

light = Light(init_camera_pos)
# Main Loop

clock = pygame.time.Clock()
selected_index = -1
axis = -1
last_magnitude = 1
offset = Vector3([0.0,0.0,0.0])
initial_transform = Transform()
running = True
render_mode = False
transform_from_gizmo = False

while running:
	
	time_delta = clock.tick(60)/1000.0
	
	
	for event in pygame.event.get():
		
		manager.update(event)
		
		if event.type == pygame.QUIT:
			running = False
			
		if event.type == MOUSEBUTTONUP:
			if event.button == 1 and axis != -1:
				transform_from_gizmo = False
				gizmo.visible = True
				
		elif (event.type == MOUSEBUTTONDOWN):

			pos = event.pos
			button = event.button
			
			if button == 1:
				
				if len(mesh_list):
					selected_index, axis = get_selected_mesh_index(mesh_list, camera, (pos[0],height - pos[1]))
					
					gizmo.visible = True if selected_index != -1 else False
				
					if selected_index != -1 and axis != -1:
						transform_from_gizmo = True
						gizmo.visible = False
						#gizmo.transform = mesh_list[selected_index].transform
				
				if selected_index >= 0:
					selected_mesh = mesh_list[selected_index]
					if gizmo.mode == "scale" or gizmo.mode == "rot":
						normal = -np.array(camera.pos)
					else:
						normal = Vector3([0.0,0.0,1.0]) if axis == 0 or axis == 1 else -np.array(camera.pos)
					plane = pyrr.plane.create_from_position(position = mesh_list[selected_index].transform.pos, normal = normal)
					offset = camera.ray_cast(camera.screen_to_world_coordinates(pos) - camera.pos, plane) - selected_mesh.transform.pos
					initial_transform = selected_mesh.transform.copy()
		
		elif event.type == KEYDOWN:
			key = event.key
			if key == K_r:
				gizmo.mode = "rot"
				
			if key == K_g:
				gizmo.mode = "pos"
				
			if key == K_s:
				gizmo.mode = "scale"
				
			if key == K_SPACE:
				camera.reset()
				light.pos = camera.pos
				gizmo.axis.transform.scale = Vector3([1.0, 1.0, 1.0])
				
			if key == K_DELETE:
				deleting_mesh = mesh_list[selected_index]
				mesh_list.remove(deleting_mesh)
				del deleting_mesh
				selected_index = -1
				
			if key == K_d:
				render_mode = not render_mode


		elif event.type == MOUSEMOTION:

			pos = event.pos
			delta = event.rel
			buttons = event.buttons
			mul = 1
			mod = pygame.key.get_mods()
			
			
			if transform_from_gizmo:
				
				selected_mesh = mesh_list[selected_index]
				
				if gizmo.mode == "rot":
					pass
					plane = pyrr.plane.create_from_position(position = selected_mesh.transform.pos, normal = -np.array(camera.pos))
					intersection = camera.ray_cast(camera.screen_to_world_coordinates(pos) - camera.pos, plane)
					
					#calculate rotation
					
					rotation_angle = np.arccos(np.dot(intersection, offset) / (np.linalg.norm(intersection) * np.linalg.norm(offset)))
					#rot = np.arcsin(np.dot(intersection, offset) / (np.linalg.norm(intersection) * np.linalg.norm(offset)))

					
					if axis == 0:
						selected_mesh.transform.rot = initial_transform.rot * Quaternion.from_x_rotation(rotation_angle)
					
					if axis == 1:
						selected_mesh.transform.rot = initial_transform.rot * Quaternion.from_y_rotation(rotation_angle)
						
					if axis == 2:
						selected_mesh.transform.rot = initial_transform.rot * Quaternion.from_z_rotation(rotation_angle)
					
				elif gizmo.mode == "scale":
					plane = pyrr.plane.create_from_position(position = selected_mesh.transform.pos, normal = -np.array(camera.pos))
					intersection = camera.ray_cast(camera.screen_to_world_coordinates(pos) - camera.pos, plane)

					magnitude = np.linalg.norm(intersection - selected_mesh.transform.pos) / np.linalg.norm(offset - selected_mesh.transform.pos)
					
					
					if axis == 0:
						selected_mesh.transform.scale = Vector3([magnitude * initial_transform.scale.x, selected_mesh.transform.scale.y, selected_mesh.transform.scale.z])
					
					if axis == 1:
						selected_mesh.transform.scale = Vector3([selected_mesh.transform.scale.x, magnitude * initial_transform.scale.y, selected_mesh.transform.scale.z])
						
					if axis == 2:
						selected_mesh.transform.scale = Vector3([selected_mesh.transform.scale.x, selected_mesh.transform.scale.y, magnitude * initial_transform.scale.z])
					
				else:
					normal = Vector3([0.0,0.0,1.0]) if axis == 0 or axis == 1 else -np.array(camera.pos)
					plane = pyrr.plane.create_from_position(position = selected_mesh.transform.pos, normal = normal)
					intersection = camera.ray_cast(camera.screen_to_world_coordinates(pos) - camera.pos, plane)
					
					if axis == 0:
						selected_mesh.transform.pos = Vector3([intersection[0] - offset[0], selected_mesh.transform.pos.y, selected_mesh.transform.pos.z])
					
					if axis == 1:
						selected_mesh.transform.pos = Vector3([selected_mesh.transform.pos.x, intersection[1] - offset[1], selected_mesh.transform.pos.z])
						
					if axis == 2:
						selected_mesh.transform.pos = Vector3([selected_mesh.transform.pos.x, selected_mesh.transform.pos.y, intersection[2] - offset[2]])

			# If pressed left or right shift transform more sensitive
			if mod & 2 or mod & 1:
				mul = 5

			# If mouse left clicked
			if buttons[1] == 1:
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
			if event.y > 0:
				gizmo.scale(Vector3([0.9, 0.9, 0.9]))
			else:
				gizmo.scale(Vector3([1.0 / 0.9, 1.0 / 0.9, 1.0 / 0.9]))
	
	
	context.viewport = (0, 0, width, height)
	context.clear(0.68, 0.87, 1)
	grid.render(camera, light, render_type = moderngl.LINES)
	
	for i,mesh in enumerate(mesh_list):
		mesh.render(camera, light, render_type = moderngl.TRIANGLES, selected = (i == selected_index), selection = render_mode)
		#mesh.lean_floor()
	for mesh in debug_mesh_list:
		mesh.render(camera, light, render_type = moderngl.LINES)
		
	display_area.render(camera, light, render_type = moderngl.TRIANGLES)
	
	if selected_index >= 0:
		gizmo.render(mesh_list[selected_index].transform, camera, light)
	
	
	viewport.render()
	pygame.display.flip()
	pygame.time.wait(10)

	




pygame.quit()