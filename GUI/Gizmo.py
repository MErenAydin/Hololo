from .Mesh import Mesh
from .Model import Model
from .Transform import Transform
from .Settings import Settings
from .Window import context
from pyrr import Quaternion
import numpy as np
import moderngl
import os

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
		
		settings = Settings()
		self.width = settings.width
		self.height = settings.height
		scale = self.transform.scale.copy()
		self.transform = transform
		self.transform.pos = transform.pos.copy()
		self.transform.scale = scale
		
		if self.visible:
			context.screen.color_mask = False, False, False, False
			context.clear(depth= 1.0, viewport = (self.width, self.height))
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
