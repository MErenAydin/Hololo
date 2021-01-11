
"""
	TODO:
		- Multiple object selection
		- Rotating and scaling with gizmo (and snapping with keyboard)
		- Text input for actions
		- Fix unselection of mesh while selecting transformation mode from screen
		- Implement quaternion to euler
		- Scaling gizmo with it's distance of camera
"""

import pygame
from pygame.locals import *
import moderngl
import numpy as np
from pyrr import Matrix44, Quaternion, Vector3, Vector4
import pyrr
from PIL import Image, ImageDraw, ImageChops, ImageOps, ImageFilter, ImageEnhance

from GUI import Transform, Model, Mesh, Camera, Light, Viewport, Manager, Button, Label, Frame, Gizmo, Settings
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

# Initializations

manager = Manager()
viewport = Viewport(manager)

frame = Frame((width - 200, 30), (200, height - 60), viewport, visible = False)

btn1 = Button((20,height - 40 - 40), (40, 40), "Quit", viewport, image_path = "Textures/quit.png", handler = app_quit)
btn2 = Button((20,height - 40 - 100), (40, 40), "Render", viewport, image_path = "Textures/export.png", handler = render)
btn3 = Button((20,height - 40 - 160), (40, 40), "Load", viewport, image_path = "Textures/import.png", handler = load)
btn4 = Button((20,height - 40 - 220), (40, 40), "Scale", viewport , image_path = "Textures/scale.png", handler = scale)
btn5 = Button((20,height - 40 - 280), (40, 40), "Rotate", viewport , image_path = "Textures/rotate.png", handler = rotate)
btn6 = Button((20,height - 40 - 340), (40, 40), "Move",  viewport , image_path = "Textures/move.png", handler = move)

lbl = Label((20,height - 30), (width - 40, 30), viewport)

lbl2 = Label((10,10), (180, 20), frame, "Transform:")
lbl3 = Label((10,40), (180, 20), frame, "   Position:")
pos_label = Label((10,70), (180, 20), frame)
lbl4 = Label((10,100), (180, 20), frame, "   Rotation:")
rot_label = Label((10,130), (180, 20), frame)
lbl5 = Label((10,160), (180, 20), frame, "   Scale:")
scale_label = Label((10,190), (180, 20), frame)

mesh_list = []
debug_mesh_list = []

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
render_mode = False
transform_from_gizmo = False

running = True

while running:
	
	time_delta = clock.tick(60)/1000.0
	
	for event in pygame.event.get():
		
		manager.update(event)
		lbl.text = "{} {} {} {}".format(manager.action, manager.axis, manager.operation, manager.result)
		
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
		frame.visible = True
		t = mesh_list[selected_index].transform
		pos_label.text = "      ({:.2f}, {:.2f}, {:.2f})".format(t.pos.x, t.pos.y, t.pos.z)
		yaw, pitch, roll = t.get_euler()
		rot_label.text = "      ({:.2f}, {:.2f}, {:.2f})".format(yaw * 180 / np.pi, pitch * 180 / np.pi, roll * 180 / np.pi)
		scale_label.text = "      ({:.2f}, {:.2f}, {:.2f})".format(t.scale.x, t.scale.y, t.scale.z)
	
	else:
		frame.visible = False
	
	viewport.render()
	pygame.display.flip()
	pygame.time.wait(10)

	




pygame.quit()