from PIL import Image, ImageOps, ImageFont
from .Texture import Texture
from .TextTexture import TextTexture, Alignment
from .Window import context

class Label():
	def __init__(self, rect_pos, rect_size, viewport, label_text = " ", image_path = None,
				font ="Font/OpenSans-Regular.ttf", font_size = 16, text_color = (0, 0, 0),
				alignment = Alignment.LEFT, bg_color = (255, 255, 255, 255), o_width = 2):
		self.text_color = text_color
		self.__text = label_text
		self.rect_size = rect_size
		self.rect_pos = tuple(map(lambda a,b: a+b, rect_pos, viewport.rect_pos))
		self.rect_rel_pos = rect_pos
		self.font = ImageFont.truetype(font, font_size) if "\\" in font or "/" in font else ImageFont.load(font, font_size)
		self.texture = TextTexture(self.rect_pos, rect_size, label_text, image_path, font, font_size, text_color, alignment,
		 				(10, (self.rect_size[1]- (sum(self.font.getmetrics())) - 1) // 2), bg_color)
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
