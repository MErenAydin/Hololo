import numpy as np
from pyrr import Matrix44, Quaternion, Vector3, Vector4
from .Settings import Settings
import pyrr

class Camera:
	def __init__(self, pos, look_point, up = None):
		
		settings = Settings()
		self.width = settings.width
		self.height = settings.height
		self.up = up if up is not None else Vector3([0.0, 0.0, 1.0])
		self._init_pos = pos
		self.pos = pos
		#[10, 0, 2.5]
		# self.rot = [np.arctan2(np.sqrt(self.pos[2] ** 2 + self.pos[0] ** 2), self.pos[1]),
					# np.arctan2(np.sqrt(self.pos[0] ** 2 + self.pos[1] ** 2), self.pos[2]),
					# np.arctan2(np.sqrt(self.pos[1] ** 2 + self.pos[2] ** 2), self.pos[0])]
		self.rot = [0,
					np.arctan2(np.sqrt(self.pos[0] ** 2 + self.pos[1] ** 2), self.pos[2]),
					0]
					
		self.radius = np.sqrt((pos[0] - look_point[0]) ** 2 + (pos[1] - look_point[1]) ** 2 + (pos[2] - look_point[2]) ** 2)
		self.look_point = look_point
		
		self.view = Matrix44.look_at(pos, look_point, self.up)
		self.projection = Matrix44.perspective_projection(45.0, self.width / self.height, 0.1, 1000.0)
		
		self.__changed = True
	
	def get_view_matrix(self):
		if self.__changed:
			self.view = Matrix44.look_at(list(self.pos), self.look_point, self.up)
			self.__changed = False
		return self.view
		
	def rotate(self, rotation_vector):
		self.rot = [a+b for a, b in zip(self.rot, [x / 250.0 for x in rotation_vector])]
		self.rot[1] = np.clip(self.rot[1], 0.1, np.pi - 0.1)
		
		self.pos = [np.sin(self.rot[1]) * np.cos(self.rot[2]), np.sin(self.rot[1]) * np.sin(self.rot[2]) , np.cos(self.rot[1])]
		self.pos = [a* self.radius for a in self.pos]
		
		self.__changed = True
 		
	def distance(self, raw_scroll):
		delta = 0.9
		if raw_scroll > 0:
			self.radius *= delta
		elif raw_scroll < 0:
			self.radius /= delta
			
		self.radius = np.clip(self.radius, 3, 50)
		self.pos = [np.sin(self.rot[1]) * np.cos(self.rot[2]), np.sin(self.rot[1]) * np.sin(self.rot[2]) , np.cos(self.rot[1])]
		self.pos = [a* self.radius for a in self.pos]
		self.__changed = True
		
	def reset(self):
		self.pos = self._init_pos
		self.rot = [0,
					np.arctan2(np.sqrt(self.pos[0] ** 2 + self.pos[1] ** 2), self.pos[2]),
					0]
		self.radius =  np.sqrt((self.pos[0] - self.look_point[0]) ** 2 + (self.pos[1] - self.look_point[1]) ** 2 + (self.pos[2] - self.look_point[2]) ** 2)
		self.__changed = True
		
	def screen_to_world_coordinates(self, mouse_pos):
		x = ((mouse_pos[0]) / float(self.width)) * 2 -1
		y = ((self.height - mouse_pos[1]) / float(self.height)) * 2 -1
		z = 0.0
		w = 1.0
		
		
		pv = self.projection * self.get_view_matrix()
		
		t = pv.inverse * Vector4([x,y,z,w])
		return Vector3([t.x, t.y , t.z ]) / t.w
		
	def world_to_screen_coordinated(self, transform):
		screen_pos = self.projection * self.get_view_matrix() * transform.get_transformation_matrix() * Vector4([0.0,0.0,0.0,1.0])
		screen_pos = screen_pos / screen_pos.w
		return Vector3([screen_pos.x, screen_pos.y, screen_pos.z])
		
	def ray_cast(self, direction, plane):
		ray = pyrr.ray.create(self.pos, direction)
		intersection = pyrr.geometric_tests.ray_intersect_plane(ray, plane)
		return intersection


class Light:
	def __init__(self, pos, color = (1.0, 1.0, 1.0)):
		self.pos = pos
		self.color = color