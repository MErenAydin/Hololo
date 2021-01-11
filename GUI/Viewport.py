from PIL import Image, ImageChops
from .Settings import Settings
from .Window import context
import pygame
import moderngl
import numpy as np

class Viewport:
	
	def __init__(self, manager, v_shader_path = "Shaders/texture_v.shader", f_shader_path = "Shaders/texture_f.shader"):
		
		settings = Settings()
		self.__image = Image.new("RGBA", (settings.width, settings.height), (0,0,0,0))
		self.manager = manager
		self.font = pygame.font.Font("Font/OpenSans-Regular.ttf", 16)
		vertices = np.array([
			0.0, 0.0, 0.0, 1.0,
			settings.width, 0.0, 1.0, 1.0,
			0.0, settings.height, 0.0, 0.0,
			0.0, settings.height, 0.0, 0.0,
			settings.width, 0.0, 1.0, 1.0,
			settings.width, settings.height, 1.0 ,0.0
		])
		
		self.program = context.program( 
			vertex_shader = open(v_shader_path).read(),
			fragment_shader = open(f_shader_path).read(),
			)
			
		#self.program['RenderMode'].value = moderngl.TEXTURE_MODE
		
		self.texture = context.texture(self.image.size, 4, self.image.tobytes())
		
		self.texture.use(0)
		
		self.w_size = self.program["w_size"]
		self.w_size.write(np.array([settings.width,settings.height]).astype('f4').tobytes())
		
		self.vbo = context.buffer(vertices.astype('f4').tobytes())
		self.vao = context.simple_vertex_array(self.program, self.vbo, 'in_vert', 'in_text')
		
	def add_image(self, img, pos):
		temp = self.image.copy()
		temp.paste(img, pos)
		self.image = temp
		
	def get_image(self):	
		return self.__image
		
	def set_image(self, value):
		diff = ImageChops.difference(self.__image.copy().convert("RGB"), value.copy().convert("RGB"))
		
		if diff.getbbox():
			self.__image = value
			self.texture.write(self.__image.tobytes())
			self.texture.use(0)
		
	def get_concat_h(self, im1, im2):
		dst = Image.new('RGBA', (im1.width + im2.width, im1.height))
		dst.paste(im1, (0, 0))
		dst.paste(im2, (im1.width, 0))
		return dst
		
	
	image = property(get_image, set_image)
	
	def render(self):
		self.vao.render(moderngl.TRIANGLES)