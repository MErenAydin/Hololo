import pygame
from pygame.locals import *
import pyassimp
import moderngl
import numpy as np
import struct
from pyrr import Matrix44,Quaternion,Vector3
import pygame_gui
from PIL import Image, ImageDraw, ImageChops

import tkinter as tk
from tkinter import filedialog as fd 
from tkinter import messagebox as mbox

root = tk.Tk()
root.withdraw()

width, height = 1280, 720

class Transform:
	def __init__(self, pos, rot, scale):
		self.pos = list(pos)
		self.rot = list(rot)
		self.scale_val = scale

	def move(self, pos):
		self.pos = [a+b for a,b in zip(pos,self.pos)]

	def rotate(self, rot):
		self.rot = [a+b for a,b in zip(rot,self.rot)]
	
	def scale(self, scale):
		self.scale = scale

class Mesh(Transform):
	def __init__(self, scene, pos = (0.0,0.0,0.0), rot = (0.0,0.0,0.0), scale = 1.0, mesh_index = 0):
		super().__init__(pos, rot, scale)
		self.scene = scene
		self.normals = scene.meshes[mesh_index].normals
		self.vertices = scene.meshes[mesh_index].vertices
		self.model_mat = Matrix44.from_translation(np.array(pos))
		

		vertices = np.append(self.vertices, self.normals,1)
		self.min_z = vertices[:,2].min()
		flatten = [j for i in vertices for j in i]

		self.context = Context(scale, flatten , pos, light_pos = (60, -45, 50))

	def move(self, x, y, z):
		super().move((x,y,z))
		self.model_mat = Matrix44.from_translation(np.array([x,y,z]))
	
	def lean_floor(self):
		self.model_mat = Matrix44.from_translation(np.array([self.pos[0], self.pos[1], -self.min_z]))
	
	def move_relative(self, x, y, z):
		
		super().move((float(x),float(y),float(z)))
		self.model_mat *= Matrix44.from_translation(np.array([float(x),float(y),float(z)]))
	
	def rotate(self, x, y, z):
		super().rotate((x,y,z))
		self.model_mat = Matrix44.from_eulers(np.array([x,y,z]))
		
	def rotate_relative(self, x, y, z):
		super().rotate((x,y,z))
		self.model_mat *= Matrix44.from_eulers(np.array([x,y,z]))

	def scale(self, scale):
		super().scale(scale)
		context._scale.value = scale

	def render(self, color = (.7, .5, .3 , 1.0)):
		proj = Matrix44.perspective_projection(45.0, width / height, 0.1, 1000.0)
		self.context._projection.write(proj.astype('float32').tobytes())
		self.context._view.write(camera.look_at.astype('float32').tobytes())
		self.context._rotation.write(rotate.astype('float32').tobytes())
		self.context._model.write(self.model_mat.astype('float32').tobytes())
		self.context._color.value = color
		self.context.vao.render(moderngl.TRIANGLES)

class Context:
	def __init__(self):
		pass
	def __init__(self, scale, flatten, pos, light_pos = (0,0,0), light_color = (1.0,1.0,1.0), v_shader_path = "D:/Code/Python/Hololo/Shaders/model_v.shader" , f_shader_path = "D:/Code/Python/Hololo/Shaders/model_f.shader"):
		self.program = context.program(
			vertex_shader = open(v_shader_path).read(),
			fragment_shader = open(f_shader_path).read(),
			)
			
		context.enable(moderngl.DEPTH_TEST)
		context.enable(moderngl.BLEND)
		context.enable(moderngl.CULL_FACE)
		context.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)

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

		self.vbo = context.buffer(struct.pack("{0:d}f".format(len(flatten)),*flatten))
		self.vao = context.simple_vertex_array(self.program, self.vbo, 'aPos','aNormal')

		context.enable(moderngl.DEPTH_TEST)
		context.enable(moderngl.BLEND)
		context.enable(moderngl.CULL_FACE)
		context.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)

class Grid(Transform):
	def __init__(self, size, steps, pos = (0.0,0.0,0.0), scale = 1.0, offset = 0, v_shader_path = "Shaders/grid_v.shader", f_shader_path = "Shaders/grid_f.shader"):
		super().__init__(pos, (0.0,0.0,0.0), scale)
		u = np.repeat(np.linspace(-size, size, steps), 2)
		v = np.tile([-size, size], steps)
		w = np.zeros(steps * 2)
		w.fill(offset)
		vertices = np.concatenate([np.dstack([u, v, w]), np.dstack([v, u, w])])

		self.program = context.program(
			vertex_shader = open(v_shader_path).read(),
			fragment_shader = open(f_shader_path).read(),
			)
		
		
		self._mvp = self.program["Mvp"]
		self._rot = self.program["Rot"]
		self._scale = self.program["Scale"]
		
		self.vbo = context.buffer(vertices.astype('f4'))
		self.vao = context.simple_vertex_array(self.program, self.vbo, 'in_vert')
		
		self._scale.value = 1.0
		self._rot.write(Matrix44.identity().astype('float32').tobytes())

	def render(self, view):
		projection = Matrix44.perspective_projection(45.0, width / height, 0.1, 1000.0)
		self._mvp.write((projection * view).astype('float32').tobytes())
		
		self.vao.render(moderngl.LINES)

class Camera(Transform):
	def __init__(self, pos, look_point, up = (0.0, 0.0, 1.0)):
		super().__init__(pos, (0,0,0), 1.0)
		self._init_pos = list(pos)
		self.pos = list(pos)
		self.rot = [np.arctan2(np.sqrt(self.pos[2] ** 2 + self.pos[0] ** 2), self.pos[1]),
					np.arctan2(np.sqrt(self.pos[0] ** 2 + self.pos[1] ** 2), self.pos[2]),
					np.arctan2(np.sqrt(self.pos[1] ** 2 + self.pos[2] ** 2), self.pos[0])]
		self.up = list(up)
		self.radius = np.sqrt((pos[0] - look_point[0]) ** 2 + (pos[1] - look_point[1]) ** 2 + (pos[2] - look_point[2]) ** 2)
		self.look_point = look_point
		self.look_at = Matrix44.look_at(pos, look_point, up)
	
	def update(self):
		self.look_at = Matrix44.look_at(self.pos, self.look_point, self.up)
		
	def rotate(self, rotation_vector):
		self.rot = [a+b for a, b in zip(self.rot, [x / 250.0 for x in rotation_vector])]
		self.rot[1] = np.clip(self.rot[1], 0.1, np.pi - 0.1)
		
		self.pos = [np.sin(self.rot[1]) * np.cos(self.rot[2]), np.sin(self.rot[1]) * np.sin(self.rot[2]) , np.cos(self.rot[1])]
		self.pos = [a* self.radius for a in self.pos]
		
		self.update()
	
	def distance(self, raw_scroll):
		delta = 0.9
		if raw_scroll > 0:
			self.radius *= delta
		elif raw_scroll < 0:
			self.radius /= delta
			
		self.radius = np.clip(self.radius, 3, 50)
		self.pos = [np.sin(self.rot[1]) * np.cos(self.rot[2]), np.sin(self.rot[1]) * np.sin(self.rot[2]) , np.cos(self.rot[1])]
		self.pos = [a* self.radius for a in self.pos]
		self.update()
	
	def reset(self):
		self.pos = self._init_pos
		self.rot = [np.arctan2(np.sqrt(self.pos[2] ** 2 + self.pos[0] ** 2), self.pos[1]),
					np.arctan2(np.sqrt(self.pos[0] ** 2 + self.pos[1] ** 2), self.pos[2]),
					np.arctan2(np.sqrt(self.pos[1] ** 2 + self.pos[2] ** 2), self.pos[0])]
		self.radius =  np.sqrt((self.pos[0] - self.look_point[0]) ** 2 + (self.pos[1] - self.look_point[1]) ** 2 + (self.pos[2] - self.look_point[2]) ** 2)
		self.update()
	
class Viewport():
	
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
		
class Button():

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

class Manager():
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
	for name in names:
		try:
			scene = pyassimp.load(name)
			mesh_list.append(Mesh(scene, pos = (0.0,0.0,0.0)))
		except:
			mbox.showerror("Load Error" , "Could not load " + name)
# Initialization of Window


pygame.init()

#[print(a) for a in sorted(pygame.font.get_fonts())]

#font = pygame.font.SysFont("OpenSans-Light.ttf", 50)
font = pygame.font.Font("Font\OpenSans-Regular.ttf", 16)
# img = font.render('The quick brown fox jumps over the lazy dog', True, (0,0,255))

# string_image = pygame.image.tostring(img, "RGBA", False)
# img = Image.frombytes("RGBA", img.get_size(), string_image)



window = pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
pygame.display.set_caption("Hololo")

context = moderngl.create_context()

#texture = Texture((0,0), img)

manager = Manager()

viewport = Viewport(manager)

btn = Button((20,height - 40 -80), (100, 40), "Render", "Render", viewport, handler = render)

btn2 = Button((20,height - 40 - 20), (100, 40), "Quit", "Quit", viewport, handler = app_quit)

btn3 = Button((20,height - 40 - 140), (100, 40), "Load", "Load", viewport, handler = load)

# Testing and Importing Meshes With Assimp (https://www.assimp.org)
mesh_list = []

scene = pyassimp.load("Template/display_area.stl")
mesh_list.append(Mesh(scene, pos = (0.0,0.0,0.0)))


grid = Grid(5,11)

init_camera_pos = (10.0, 0.0, 2.5)
origin = (0.0,0.0,0.0)
camera = Camera(init_camera_pos, origin)

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

clock = pygame.time.Clock()

running = True

while running:

	time_delta = clock.tick(60)/1000.0
	
	
	for event in pygame.event.get():
	
		manager.update(event)
		if event.type == pygame.QUIT:
			running = False
			
			
		elif event.type == pygame.USEREVENT:
			if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
				if event.ui_element == hello_button:
					print('Hello World!')

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

					# Clear the event buffer
					pygame.event.clear()

		# If mouse scroll moved
		elif event.type == MOUSEWHEEL:
				
			camera.distance(event.y)
	
	
	context.viewport = (0, 0, width, height)
	context.clear(0.7, 0.7, 0.9)
	grid.render(camera.look_at)
	
	
	for i,mesh in enumerate(mesh_list):
		if i != 0:
			mesh.render(color = (.7, .5, i * 0.2 , 1.0))
		mesh.lean_floor()
	
	mesh_list[0].render(color = (0.0, 0.8 , 0.0 , 0.25))
	
	viewport.render()
	pygame.display.flip()
	pygame.time.wait(10)

	



pygame.quit()