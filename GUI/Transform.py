from pyrr import Matrix44, Quaternion, Vector3, Vector4

class Transform:
	def __init__(self, pos = None, rot = None, scale = None):
		
		self.__model_mat = Matrix44.identity()
		
		self.__pos = pos if pos is not None else Vector3([0.0,0.0,0.0])
		self.__rot = rot if rot is not None else Quaternion.from_matrix(Matrix44.identity())
		self.__scale = scale if scale is not None else Vector3([1.0,1.0,1.0])
		# Variable for reducing calculation of transformation matrix by checking if any variable changed
		self.__changed = True
		self.get_transformation_matrix()
		
	def __str__(self):
		return "Position: {}\nRotation: {}\nScale: {}".format(self.pos,self.rot,self.scale)
		
	def get_transformation_matrix(self):
		if self.__changed:
			matrix = Matrix44.from_translation(self.pos)
			matrix *= Matrix44.from_scale(self.scale)
			self.__model_mat = matrix * Matrix44.from_quaternion(self.rot)
			
			self.__changed = False
		return self.__model_mat
		
	# Getters and setters for properties
	def get_pos(self):
		return self.__pos
		
	def set_pos(self, value):
		self.__pos = value
		self.__changed = True
		
	def get_rot(self):
		return self.__rot
		
	def set_rot(self, value):
		self.__rot = value
		self.__changed = True
		
	def get_scale(self):
		return self.__scale
		
	def set_scale(self, value):
		self.__scale = value
		self.__changed = True
		
	# Properties
	pos = property(get_pos, set_pos)
	rot = property(get_rot, set_rot)
	scale = property(get_scale, set_scale)
	
	# TODO: Will be implemented
	def get_euler(self):
		return self.__rot.axis
	
	# Returns copy of instance
	def copy(self):
		return Transform(self.pos.copy(), self.rot.copy(), self.scale.copy())