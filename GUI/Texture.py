from PIL import Image, ImageOps
from .Settings import Settings
from .Window import context
import moderngl
import numpy as np

class Texture:
	def __init__(self, rect_pos, rect_size, image_or_path = None, bg_color = (0,0,0,0),
				v_shader_path = "Shaders/texture_v.shader", f_shader_path = "Shaders/texture_f.shader"):
		
		settings = Settings()

		if isinstance(image_or_path, type(Image)):
			self.__image = image_or_path
		else:
			self.__image = ImageOps.flip(self.get_image_from_file(image_or_path, rect_size)) if image_or_path is not None else Image.new("RGBA", rect_size, bg_color)
		self.rect_pos = rect_pos
		self.rect_size = rect_size
		#self.manager = manager
		#self.font = pygame.font.Font("Font/OpenSans-Regular.ttf", 16)
		flipped_y = settings.height - rect_pos[1]

		vertices = np.array([
			rect_pos[0] + rect_size[0],	flipped_y, 				1.0, 1.0,
			rect_pos[0], 				flipped_y, 				0.0, 1.0,
			rect_pos[0], 				flipped_y - rect_size[1],	0.0, 0.0,
			rect_pos[0] + rect_size[0],	flipped_y, 				1.0, 1.0,
			rect_pos[0], 				flipped_y - rect_size[1],	0.0, 0.0,
			rect_pos[0] + rect_size[0],	flipped_y - rect_size[1],	1.0, 0.0
		])
		
		self.program = context.program( 
			vertex_shader = open(v_shader_path).read(),
			fragment_shader = open(f_shader_path).read(),
			)
			
		self.visible = True
		self.texture = context.texture(self.image.size, 4, self.image.tobytes())
		self.texture.write(self.__image.tobytes())
		
		self.w_size = self.program["w_size"]
		self.w_size.write(np.array([settings.width,settings.height]).astype('f4').tobytes())
		
		self.vbo = context.buffer(vertices.astype('f4').tobytes())
		self.vao = context.simple_vertex_array(self.program, self.vbo, 'in_vert', 'in_text')

		#self.manager.textures.append(self)
		
	def get_image_from_file(self, path, size):
		image = Image.open(path)
		image = image.resize(size, Image.ANTIALIAS)
		return image

	def add_image(self, img, pos):
		temp = self.image.copy()
		temp.paste(img, pos)
		self.image = temp
		
	def get_image(self):	
		return self.__image
		
	def set_image(self, value):
		self.__image = ImageOps.flip(value)
		self.texture.write(self.__image.tobytes())

	image = property(get_image, set_image)
	
	def render(self):
		if self.visible:
			self.texture.use()
			self.vao.render(moderngl.TRIANGLES)