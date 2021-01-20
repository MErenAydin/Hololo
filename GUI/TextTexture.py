from enum import Enum
from PIL import Image, ImageDraw, ImageFont
from .Texture import Texture

class Alignment(Enum):
	LEFT_TOP = 1
	CENTER_TOP = 2
	RIGHT_TOP = 3
	LEFT = 4
	CENTER_MID = 5
	RIGHT = 6
	LEFT_BOTTOM = 7
	CENTER_BOTTOM = 8
	RIGHT_BOTTOM = 9	

class TextTexture(Texture):

	def __init__(self, rect_pos, rect_size, text, image_or_path = None, font = "Font/OpenSans-Regular.ttf",
		font_size = 16, font_color = (0, 0, 0, 255), alignment = Alignment.LEFT, margin = (10,0) , bg_color = (255,255,255,255),
		v_shader_path = "Shaders/texture_v.shader", f_shader_path = "Shaders/texture_f.shader"):
		
		super().__init__(rect_pos, rect_size, image_or_path = image_or_path, bg_color = bg_color, v_shader_path = v_shader_path, f_shader_path = f_shader_path)
		self.__text = text
		self.__font_path = font
		self.__font_size = font_size
		self.__alignment = alignment

		self.margin = margin
		self.font = ImageFont.truetype(font, font_size) if "\\" in font or "/" in font else ImageFont.load(font, font_size)
		self.font_color = font_color
		self.bg_image = self.image.copy()
		self.update_image()
		self.__changed = False

	def update_image(self):
		image = self.bg_image.copy()
		draw = ImageDraw.Draw(image)

		draw.text(self.margin, self.text, font = self.font, fill = self.font_color)

		self.image = image
		

	def get_changed(self):
		return self.__changed
	
	def set_changed(self, value):
		self.update_image()
		self.__changed = False
	
	changed = property(get_changed, set_changed)

	def get_text(self):
		return self.__text
	
	def set_text(self, value):
		if self.__text != value:
			self.__text = value
			self.changed = True
	
	text = property(get_text, set_text)

	def get_font_path(self):
		return self.__font_path
	
	def set_font_path(self, value):
		self.__font_path = value
		if "/" in self.font_path or "\\" in self.font_path: 
			self.font = ImageFont.truetype(self.font_path, self.font_size)
		elif self.font_path is not None:
			self.font = ImageFont.load(self.font_path, self.font_size)
		self.changed = True
	
	font_path = property(get_font_path, set_font_path)

	def get_font_size(self):
		return self.__font_size
	
	def set_font_size(self, value):
		self.__font_size = value
		self.changed = True

	font_size = property(get_font_size, set_font_size)

	def get_alignment(self):
		return self.__alignment
	
	def set_alignment(self, value):
		self.__alignment = value
		self.changed = True
	
	alignment = property(get_alignment, set_alignment)