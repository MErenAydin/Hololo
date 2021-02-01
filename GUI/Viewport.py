from PIL import Image, ImageChops
from .Settings import Settings
from .Frame import Frame
from .Window import context
import moderngl
import numpy as np

class Viewport:
	
	def __init__(self, manager, v_shader_path = "Shaders/texture_v.shader", f_shader_path = "Shaders/texture_f.shader"):
		
		self.elements = []

		settings = Settings()
		self.rect_pos = (0,0)
		self.rect_rel_pos = (0,0)
		self.manager = manager
		self.visible = True

	def append_texture(self, texture):
		self.elements.append(texture)
	
	def render(self):
		#if self.visible:
		context.disable(moderngl.DEPTH_TEST)
		context.disable(moderngl.CULL_FACE)
		for element in self.elements:
			if isinstance(element, Frame):
				element.render()
			else:
				element.texture.render()
		context.enable(moderngl.DEPTH_TEST)
		context.enable(moderngl.CULL_FACE)

	def add_image(self,image,rect_size):
		pass
