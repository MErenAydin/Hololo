from PIL import Image
from .Texture import Texture
from .Window import context
import pygame

class Label():
	def __init__(self, rect_pos, rect_size, viewport, label_text = " ", image_path = None, text_color = (0, 0, 0) , bg_color = (255, 255, 255, 0), o_width = 2):
		self.text_color = text_color
		self.__text = label_text
		self.rect_size = rect_size
		self.rect_pos = tuple(map(lambda a,b: a+b, rect_pos, viewport.rect_pos))
		self.rect_rel_pos = rect_pos
		self.texture = Texture(rect_pos, rect_size, image = image_path)
		self.viewport = viewport
		self.bg_color = bg_color
		self.width = o_width
		self.image_path = image_path
		self.image = self.get_image_from_file(self.image_path, self.rect_size) if self.image_path is not None else Image.new("RGBA", self.rect_size, self.bg_color)	
		
		self.visible = True
		viewport.textures.append(self.texture)

		image = self.get_image()
		self.viewport.add_image(image, self.rect_rel_pos)
	
	def get_image_from_file(self, path, size):
		image = Image.open(path)
		image = button_image.resize(size, Image.ANTIALIAS)
		return button_image

	def get_image(self):
		image = self.image.copy()
			
		img = self.viewport.font.render(self.__text, True, self.text_color)
		string_image = pygame.image.tostring(img, "RGBA", False)
		img = Image.frombytes("RGBA", img.get_size(), string_image)
		offset = (0, self.rect_size[1] // 2 - (img.size[1] // 2))
		image.paste(img, offset)
		
		return image
	
	def set_text(self, value):
		changed = self.__text != value
		self.__text = value if value != "" else " "
		if changed:
			image = self.image.copy()
			
			img = self.viewport.font.render(self.__text, True, self.text_color)
			string_image = pygame.image.tostring(img, "RGBA", False)
			img = Image.frombytes("RGBA", img.get_size(), string_image)
			offset = (0, self.rect_size[1] // 2 - (img.size[1] // 2))
			image.paste(img, offset)
			
			self.viewport.add_image(image, self.rect_rel_pos)
		
		
	def get_text(self):
		return self.__text
		
	text = property(get_text, set_text)
