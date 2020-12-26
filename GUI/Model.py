import moderngl
import struct
from .Transform import Transform
from .Window import context

class Model:
	def __init__(self, mesh, transform = None, color = (.7, .5, .3 , 1.0), v_shader_path = "Shaders/model_v.shader" , f_shader_path = "Shaders/model_f.shader"):
		
		
		self.transform = transform if transform is not None else Transform()
		self.mesh = mesh
		
		self.v_shader_path = v_shader_path
		self.f_shader_path = f_shader_path
		
		self.program = context.program(
			vertex_shader = open(v_shader_path).read(),
			fragment_shader = open(f_shader_path).read(),
			)
			
		self.color = color
		
		self._model = self.program['model']
		self._view = self.program['view']
		self._projection = self.program['projection']
		self._color = self.program['objectColor']
		self._light_pos = self.program['lightPos']
		self._light_color = self.program['lightColor']
		self._selection = self.program['selection']
		self._grow = self.program['grow']
		
		self.vbo = context.buffer(struct.pack("{0:d}f".format(len(self.mesh.vertices)), *self.mesh.vertices))
		# self.vbo = context.buffer(self.mesh.vertices.astype("f4"))
		#self.ebo = context.buffer(self.mesh.indices.astype("uint32").tobytes())
		self.vao = context.simple_vertex_array(self.program, self.vbo, 'aPos','aNormal')
		
	def render(self, camera,  light, render_type = moderngl.TRIANGLES, selection = False , selected = False):
		
		self._projection.write(camera.projection.astype('float32').tobytes())
		self._view.write(camera.get_view_matrix().astype('float32').tobytes())
		self._model.write(self.transform.get_transformation_matrix().astype('float32').tobytes())
		self._grow.value = 0.0 if selection else 0.0 
		self._color.value = self.color if not selected else tuple([i + 0.2 for i in self.color])
		self._light_color.value = light.color
		self._light_pos.value = tuple(light.pos)
		self._selection.value = selection
		self.vao.render(render_type)
	
	def reload(self):
		self.vbo.write(struct.pack("{0:d}f".format(len(self.mesh.vertices)), *self.mesh.vertices))