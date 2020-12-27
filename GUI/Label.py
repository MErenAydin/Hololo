from PIL import Image
import pygame

class Label():
	def __init__(self, rect_pos, rect_size, viewport, label_text = "", image_path = None, text_color = (0, 0, 0) , bg_color = (255, 255, 255, 0), o_width = 2):
		self.text_color = text_color
		self.__text = label_text
		self.rect_size = rect_size
		self.rect_pos = rect_pos
		self.viewport = viewport
		self.bg_color = bg_color
		self.width = o_width
		self.image_path = image_path
		self.image = self.get_image_from_file(self.image_path, self.rect_size) if self.image_path is not None else Image.new("RGBA", self.rect_size, self.bg_color)	
		
		image = self.get_image()
		self.viewport.add_image(image, self.rect_pos)
	
	def get_image_from_file(self, path, size):
		image = Image.open(path)
		image = button_image.resize(size, Image.ANTIALIAS)
		return button_image

	def get_image(self):
		image = self.image.copy()
			
		img = self.viewport.font.render(self.__text, True, self.text_color)
		string_image = pygame.image.tostring(img, "RGBA", False)
		img = Image.frombytes("RGBA", img.get_size(), string_image)
		offset = (self.rect_size[0] // 2 - (img.size[0] // 2), self.rect_size[1] // 2 - (img.size[1] // 2))
		image.paste(img, offset)
		
		return image

	# def clear(self):
	# 	if self.image_path != None:
	# 		self.text_input_image = Image.open(self.image_path, "RGBA")
	# 	else:
	# 		self.text_input_image = Image.new("RGBA", self.rect_size, self.bg_color)
	# 		draw = ImageDraw.Draw(self.text_input_image)
	# 		draw.rectangle(((self.width // 2 - 1, self.width // 2 - 1), (self.rect_size[0] - (self.width // 2), self.rect_size[1] - (self.width // 2))), fill= self.bg_color, outline = (0,0,0,255), width = self.width)
	# 		self.text_input_image = self.text_input_image.resize(self.rect_size)
	
	def set_text(self, value):
		changed = self.__text != value
		self.__text = value
		if changed:
			image = self.image.copy()
			
			img = self.viewport.font.render(self.__text, True, self.text_color)
			string_image = pygame.image.tostring(img, "RGBA", False)
			img = Image.frombytes("RGBA", img.get_size(), string_image)
			offset = (self.rect_size[0] // 2 - (img.size[0] // 2), self.rect_size[1] // 2 - (img.size[1] // 2))
			image.paste(img, offset)
			
			self.viewport.add_image(image, self.rect_pos)
		
		
	def get_text(self):
		return self.__text
		
	text = property(get_text, set_text)
