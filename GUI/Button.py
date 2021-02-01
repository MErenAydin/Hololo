from PIL import Image, ImageDraw, ImageEnhance, ImageOps, ImageFont
from .Texture import Texture

class Button:

	def __init__(self, rect_pos, rect_size, button_name, viewport, button_text = "",\
				handler = None, image_path = None, font ="Font/OpenSans-Regular.ttf", font_size = 16,\
				text_color = (0, 0, 0) , bg_color = (220, 220, 220, 255), o_width = 5 , three_D = False):
		
		self.__hover = False
		self.__clicked = False
		self.font = ImageFont.truetype(font, font_size) if "\\" in font or "/" in font else ImageFont.load(font, font_size)
		
		self.rect_pos = tuple(map(lambda a,b: a+b, rect_pos, viewport.rect_pos))
		self.rect_rel_pos = rect_pos
		self.rect_size = rect_size

		self.texture = Texture(rect_pos, rect_size, image_or_path = image_path)
		self.button_name = button_name
		self.button_text = button_text
		self.viewport = viewport
		self.image_path = image_path
		self.text_color = text_color
		self.bg_color = bg_color
		self.width = o_width
		self.three_D = three_D
		self.handler = handler
		
		self.viewport.elements.append(self)
		viewport.manager.buttons[button_name] = self
		
	# 	self.image = self.get_image(self.bg_color, self.text_color) if self.image_path is None else self.get_image_from_file(self.image_path, self.rect_size)
		
	# def get_image_from_file(self, path, size):
	# 	button_image = Image.open(path)
	# 	button_image = button_image.resize(size, Image.ANTIALIAS)
		
	# 	return button_image
	
	# def get_image(self, bg_color , text_color, clicked = False):
		
	# 	button_image = Image.new("RGBA", self.rect_size, bg_color)
	# 	draw = ImageDraw.Draw(button_image)
	# 	if self.three_D:
	# 		lc = [a + 30 for a in bg_color[0:3]]
	# 		lc.append(bg_color[3])
	# 		dc = [a - 30 for a in bg_color[0:3]]
	# 		dc.append(bg_color[3])
	# 		if clicked:
	# 			temp = lc
	# 			lc = dc
	# 			dc = temp
	# 		f = list(bg_color[0:3])
	# 		f.append(bg_color[3])
			
	# 		draw.rectangle(((0, 0),(button_image.size[0] - 1, button_image.size[1] - 1)), fill = tuple(f), outline = tuple(dc), width = self.width)
	# 		draw.polygon(((0,0), (0,button_image.size[1] - 1), (self.width - 1, button_image.size[1] - self.width  ), (self.width - 1, self.width - 1), (button_image.size[0] - self.width, self.width - 1 ),(button_image.size[0] - 1, 0)), fill = tuple(lc))
				
		
	# 	else:
	# 		draw.rectangle(((self.width // 2 - 1, self.width // 2 - 1), (self.rect_size[0] - (self.width // 2), self.rect_size[1] - (self.width // 2))), fill= self.bg_color, outline = (0,0,0,255), width = self.width)
		
	# 	button_image = button_image.resize(self.rect_size)
		
	# 	img = self.viewport.font.render(self.button_text, True, text_color)
	# 	string_image = pygame.image.tostring(img, "RGBA", False)
	# 	img = Image.frombytes("RGBA", img.get_size(), string_image)
	# 	offset = (self.rect_size[0] // 2 - (img.size[0] // 2), self.rect_size[1] // 2 - (img.size[1] // 2))
	# 	button_image.paste(img, offset, img)
		
	# 	return button_image
		
	def get_hover(self):
		return self.__hover
		
	def set_hover(self, value):
		changed = self.hover != value
		if changed:
			self.__hover = value
			if value:
				if not self.__clicked:
					enhancer = ImageEnhance.Brightness(self.texture.image.copy())
					self.texture.image = ImageOps.flip(enhancer.enhance(1.1))

					# enhancer = ImageEnhance.Brightness(self.image.copy())
					# img = enhancer.enhance(1.1)
					# self.viewport.add_image(img, self.rect_rel_pos)
			else:
				pass
				#self.texture.image = enhancer.enhance(1 / 1.1)
		
	hover = property(get_hover, set_hover)
	
	def get_clicked(self):
		return self.__clicked
	
	def set_clicked(self, value):
		self.__clicked = value
		if value:
			if self.__hover:
				if self.handler:
					self.handler()
					
				
				#if self.three_D:
				#	img = self.get_image(self.bg_color, self.text_color, clicked = True)
				#enhancer = ImageEnhance.Brightness(img if self.three_D else self.texture.image.copy())
				#img = enhancer.enhance(0.9)
				
				#self.texture.image = img.copy()
			else:
				self.__clicked = False
				#self.viewport.add_image(self.image, self.rect_rel_pos)
		else:
			pass
			#enhancer = ImageEnhance.Brightness(self.image.copy())
			#img = enhancer.enhance(1.1)
			#self.viewport.add_image(img, self.rect_rel_pos)
		
	clicked = property(get_clicked, set_clicked)

	def set_visible(self, value):
		self.__visible = value
		self.texture.visible = value
		if not self.viewport.visible:
			self.__visible = False
			self.texture.visible = False
			
	def get_visible(self):
		return self.__visible
		
	visible = property(get_visible,set_visible)