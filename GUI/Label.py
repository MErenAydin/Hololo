from PIL import Image, ImageOps
from .Texture import Texture
from .TextTexture import TextTexture
from .Window import context
import pygame

class Label():
	def __init__(self, rect_pos, rect_size, viewport, label_text = "", image_path = None, text_color = (0, 0, 0, 255) , bg_color = (255, 255, 255, 255), o_width = 2):
		self.text_color = text_color
		self.__text = label_text
		self.rect_size = rect_size
		self.rect_pos = tuple(map(lambda a,b: a+b, rect_pos, viewport.rect_pos))
		self.rect_rel_pos = rect_pos
		self.texture = TextTexture(self.rect_pos, rect_size, self.text, font_color = text_color, margin = 0)
		self.viewport = viewport
		self.bg_color = bg_color
		self.width = o_width
		self.__visible = self.viewport.visible
		self.texture.visible = self.viewport.visible
		self.viewport.elements.append(self)

	def set_text(self, value):
		self.__text = value
		self.texture.text = value
			
	def get_text(self):
		return self.__text

	def set_visible(self, value):
		self.__visible = value
		self.texture.visible = value
		if not self.viewport.visible:
			self.__visible = False
			self.texture.visible = False
			
	def get_visible(self):
		return self.__visible
		
	visible = property(get_visible,set_visible)
	text = property(get_text, set_text)
