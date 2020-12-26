
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
import moderngl
import numpy as np
from pyrr import Matrix44,Quaternion,Vector3, Vector4
import pyrr
from PIL import Image, ImageDraw, ImageChops, ImageOps, ImageFilter, ImageEnhance

from GUI import Transform, Model, Mesh, Camera, Light, Viewport, Manager, Button, Gizmo, Settings
from GUI.Window import context

import tkinter as tk
from tkinter import filedialog as fd 
from tkinter import messagebox as mbox



root = tk.Tk()
root.withdraw()

settings = Settings()
width = settings.width
height = settings.height

def grid(size, steps):
	# Returns numpy array of vertices of square grid which has given size and steps
	u = np.repeat(np.linspace(-size, size, steps), 2)
	v = np.tile([-size, size], steps)
	w = np.zeros(steps * 2)
	return np.concatenate([np.dstack([u, v, w])[:][:][0], np.dstack([v, u, w])[:][:][0]])


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

#[print(a) for a in sorted(pygame.font.get_fonts())]

#font = pygame.font.SysFont("OpenSans-Light.ttf", 50)
# img = font.render('The quick brown fox jumps over the lazy dog', True, (0,0,255))

# string_image = pygame.image.tostring(img, "RGBA", False)
# img = Image.frombytes("RGBA", img.get_size(), string_image)


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

if settings.init_obj_path != "" and settings.init_obj_path is not None:
	mesh_list.append(Model(Mesh.from_file(settings.init_obj_path)))

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
				
			#if key == K_ENTER:
			#	#apply input text
			#	pass
				
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
				x = ((pos[0]) / float(width)) * 2 -1
				y = ((height - pos[1]) / float(height)) * 2 -1
				
				if gizmo.mode == "rot":
					screen_pos = camera.world_to_screen_coordinated(selected_mesh.transform.copy())
					dir_vector = (screen_pos.x - x, screen_pos.y - y) 
					angle = np.arctan2(dir_vector[1], dir_vector[0])
					
					
					if axis == 0:
						selected_mesh.transform.rot = initial_transform.rot * Quaternion.from_x_rotation(-angle)
					
					if axis == 1:
						selected_mesh.transform.rot = initial_transform.rot * Quaternion.from_y_rotation(-angle)
						
					if axis == 2:
						selected_mesh.transform.rot = initial_transform.rot * Quaternion.from_z_rotation(-angle)
					
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