import pyassimp
import numpy as np

class Mesh:
	def __init__(self, vertices, indices = None, normals = None):
		

		self.normals = normals if normals is not None else np.zeros((len(vertices),3))
		self.indices = indices if indices is not None else np.array(list(range(len(vertices))))
		
		vertices = np.append(vertices, self.normals,1)
		
		self.vertices = [j for i in vertices for j in i]

	
	
	@staticmethod
	def from_assimp_mesh(mesh):
		normals = mesh.normals
		vertices = mesh.vertices
		
		# vertices = np.append(vertices, normals,1)
		
		# flatten = [j for i in vertices for j in i]
		return Mesh(vertices, normals = normals)
	
	@staticmethod
	def from_file(path, mesh_index = 0):
		scene = pyassimp.load(path)
		return Mesh.from_assimp_mesh(scene.meshes[mesh_index])
		
	# def calculate_bounding_box(self):
	# 	return aabb.from_points(self.vertices)