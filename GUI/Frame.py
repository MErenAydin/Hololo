from PIL import Image, ImageChops
import pygame
import moderngl
import numpy as np

class Frame:
	
	def __init__(self, rect_pos, rect_size, viewport, image_path = None, visible = True):
		
		self.image_path = image_path
		self.__image = Image.new("RGBA", rect_size, (0,0,0,125)) if image_path is None else get_image_from_file(image_path, rect_size)
		self.rect_pos = tuple(map(lambda a,b: a+b, rect_pos, viewport.rect_pos))
		self.rect_rel_pos = rect_pos
		self.rect_size = rect_size
		self.viewport = viewport
		self.font = viewport.font
		self.manager = self.viewport.manager
		self.__visible = visible
		self.button_list = []
		
		if self.visible:
			viewport.add_image(self.image, self.rect_pos)
		
	def add_image(self, img, pos):
		temp = self.image.copy()
		temp.paste(img, pos)
		self.image = temp
		
	def get_image_from_file(self, path, size):
		frame_image = Image.open(path)
		frame_image = frame_image.resize(size, Image.ANTIALIAS)
		
		return frame_image
	
	def get_image(self):	
		return self.__image
		
	def set_image(self, value):
		self.__image = value
		if self.visible:
			self.viewport.add_image(self.__image, self.rect_rel_pos)

	def set_visible(self, value):
		self.__visible == value
		if value:
			self.viewport.add_image(self.__image, self.rect_rel_pos)
		else:
			self.viewport.add_image(Image.new("RGBA", self.rect_size, (0,0,0,0)), self.rect_rel_pos)
	
	def get_visible(self):
		return self.__visible

	visible = property(get_visible, set_visible)
	image = property(get_image, set_image)
