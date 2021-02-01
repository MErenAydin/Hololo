from PIL import Image, ImageChops
import moderngl
from .Texture import Texture
from .Window import context
from .Settings import Settings
import numpy as np

class Frame:
	
	def __init__(self, rect_pos, rect_size, viewport, image_path = None, visible = True):
		
		self.image_path = image_path
		self.rect_pos = tuple(map(lambda a,b: a+b, rect_pos, viewport.rect_pos))
		self.rect_rel_pos = rect_pos
		self.rect_size = rect_size
		self.texture = Texture(self.rect_pos, rect_size,  bg_color = (0,0,0,125))
		self.viewport = viewport
		self.manager = self.viewport.manager
		self.__visible = visible
		
		self.elements = []
		self.viewport.elements.append(self)
	
	def append_texture(self, texture):
		self.viewport.append_texture(texture)
	
	def set_visible(self, value):
		self.__visible = value
		self.texture.visible = value
		for element in self.elements:
			element.visible = value
		# if not self.viewport.visible:
		# 	self.__visible = False
		# 	self.texture.visible = False	

	def get_visible(self):
		return self.__visible
	
	visible = property(get_visible, set_visible)

	def render(self):
		self.texture.render()
		settings = Settings()
		sc = context.scissor
		context.scissor = self.rect_pos[0], settings.height - self.rect_pos[1] - self.rect_size[1], self.rect_size[0], self.rect_size[1]
		for element in self.elements:
			if isinstance(element, Frame):
				element.render()
			else:
				element.texture.render()
		context.scissor = sc
