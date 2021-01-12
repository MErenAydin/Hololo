import struct
import pyassimp
import numpy as np
from GUI import Mesh, Model, Transform
from enum import Enum
from pyrr import Vector3, Matrix44

def apply_transform(model_list):
	out_model = Model(Mesh(np.array()))
	sum = 0
	for i,model in enumerate(model_list):
		tr_matrix = model.transform.get_transformation_matrix()
		if i != 0:
			sum += len(model_list[i-1].mesh.vertices)
		for vertex in model.mesh.vertices:
			out_model.vertices.append(tr_matrix * vertex)
		out_model.indices.append([a + sum for a in model.mesh.indices])


class SITUATION(Enum):
	DEGENERATE = -1
	NO_INTERSECTION = 0
	POINT_INTERSECTION = 1
	LINE_INTERSECTION = 2
	FACE_INTERSECTION = 3

def dist_point_to_plane(point, plane):
	sn = -np.dot(plane[1], (point - plane[0]))
	sd = np.dot(plane[1], plane[1])
	sb = 0
	if sd != 0: 
		sb =  sn / sd

	#return if necessary
	nearest_point = point + sb * plane[1]
	distance = np.sqrt(np.dot(point - nearest_point, point - nearest_point))	
	
	retval = 1 if point[2] > nearest_point[2] else (0 if point[2] == nearest_point[2] else -1)
	return distance, retval

def intersect_seg_plane(segment, plane):

	u = segment[1] - segment[0]
	w = segment[0] - plane[0]

	D = np.dot(plane[1], u)
	N = -np.dot(plane[1], w)

	if (abs(D) < 0.00000001):					# segment is parallel to plane
		if (N == 0):							# segment lies in plane
			return SITUATION.LINE_INTERSECTION, segment
		else:
			return SITUATION.NO_INTERSECTION, None	# no intersection

    # they are not parallel
    # compute intersect param
	sI = N / D;
	if (sI < 0 ):
		return SITUATION.NO_INTERSECTION, None							# no intersection

	I = segment[0] + sI * u							# compute segment intersect point
	return SITUATION.POINT_INTERSECTION, I

def intersect_tri_plane(T, P):

	v0 = dist_point_to_plane(T[0],P)
	v1 = dist_point_to_plane(T[1],P)
	v2 = dist_point_to_plane(T[2],P)
	res =  np.array([v0[1], v1[1], v2[1]])


	if not res.any():
		#triangle laying on plane
		return SITUATION.FACE_INTERSECTION, T

	elif np.count_nonzero(res > 0 ) == 3 or np.count_nonzero(res < 0 ) == 3:
		#triangle not intersect with plane
		return SITUATION.NO_INTERSECTION,None

	elif (np.count_nonzero(res >= 0) == 2 and  np.count_nonzero(res < 0) == 1) or \
			(np.count_nonzero(res <= 0) == 2 and  np.count_nonzero(res > 0) == 1):
		comb = [[0,1],[1,2],[2,0]]
		seg = []
		for c in comb:
			isp = intersect_seg_plane(np.array([T[c[0]],T[c[1]]]),P)

			if isp[0] == SITUATION.POINT_INTERSECTION:
				seg.append(isp[1])
			
			elif isp[0] == SITUATION.LINE_INTERSECTION:
				return SITUATION.LINE_INTERSECTION, isp[1]

		
		return SITUATION.LINE_INTERSECTION, np.array(seg)

	else:
		for i in range(3):
			if res[i] == 0:
				return SITUATION.POINT_INTERSECTION, np.array([T[i]])

def intersections(triangles, vertices, plane_z):
	
	intsc = []
	
	
	for tri in triangles:
		col_type, collision = intersect_tri_plane(np.array([vertices[tri[0]], vertices[tri[1]], vertices[tri[2]]]), np.array([[0.,0.,plane_z],[0,0,1]]))
		#lines = np.array([vertices[tri[0]] - vertices[tri[1]], vertices[tri[1]] - vertices[tri[2]], vertices[tri[2]] - vertices[tri[0]]])
		
		if col_type == SITUATION.LINE_INTERSECTION:
			intsc.append(collision)
		
	
	return np.array(intsc)

def intersection_circle_seg(circle_center, circle_radius, pt1, pt2, full_line=False, tangent_tol=1e-9):

    (p1x, p1y), (p2x, p2y), (cx, cy) = pt1, pt2, circle_center
    (x1, y1), (x2, y2) = (p1x - cx, p1y - cy), (p2x - cx, p2y - cy)
    dx, dy = (x2 - x1), (y2 - y1)
    dr = (dx ** 2 + dy ** 2)**.5
    big_d = x1 * y2 - x2 * y1
    discriminant = circle_radius ** 2 * dr ** 2 - big_d ** 2

    if discriminant < 0:  # No intersection between circle and line
        return []
    else:  # There may be 0, 1, or 2 intersections with the segment
        intersections = [
            (cx + (big_d * dy + sign * (-1 if dy < 0 else 1) * dx * discriminant**.5) / dr ** 2,
             cy + (-big_d * dx + sign * abs(dy) * discriminant**.5) / dr ** 2)
            for sign in ((1, -1) if dy < 0 else (-1, 1))]  # This makes sure the order along the segment is correct
        if not full_line:  # If only considering the segment, filter out intersections that do not fall within the segment
            fraction_along_segment = [(xi - p1x) / dx if abs(dx) > abs(dy) else (yi - p1y) / dy for xi, yi in intersections]
            intersections = [pt for pt, frac in zip(intersections, fraction_along_segment) if 0 <= frac <= 1]
        if len(intersections) == 2 and abs(discriminant) <= tangent_tol:  # If line is tangent to circle, return just one point (as both intersections have same location)
            return [intersections[0]]
        else:
            return intersections


scene = pyassimp.load("Template/cube.stl")
triangles = scene.meshes[0].faces
vertices = scene.meshes[0].vertices

offsets = np.linspace(vertices[:,2].min(),vertices[:,2].max(), 16)

radii = np.linspace(.13, 2.83, 16) #3.87

intrsc = []
points = []
for i in range(16):

	col = intersections(triangles,vertices,offsets[i])

	for seg in col:
		for j in range(16):
			cs = intersection_circle_seg(np.array([0,0]), radii[j], (seg[0][0], seg[0][1]) , (seg[1][0], seg[1][1]))
			if len(cs) == 1:
				points.append((cs[0][0],cs[0][1],offsets[i]))
			if len(cs) == 2:
				points.append((cs[0][0],cs[0][1],offsets[i]))
				points.append((cs[1][0],cs[1][1],offsets[i]))


	intrsc.append(col)
	#print(intrsc)
	#P.append(intrsc)
	#file.writelines(str(intrsc))
	#file.write("\n\n")
#plt.plot(P[14][:,0], P[14][:,1])

intrsc = np.array([a for b in [j for i in intrsc for j in i] for a in b])

#print(intrsc[:,0][:,0] ,"\t" , intrsc[:,0][:,1])

for i in range(0,len(points),2):
	ax.scatter([points[i][0], points[i+1][0]],[points[i][1], points[i+1][1]] ,[points[i][2], points[i+1][2]])

#for i in range(0,len(intrsc),2):
#	ax.plot([intrsc[i][0], intrsc[i+1][0]],[intrsc[i][1], intrsc[i+1][1]] ,[intrsc[i][2], intrsc[i+1][2]] )
	#ax.scatter([intrsc[i][0], intrsc[i+1][0]],[intrsc[i][1], intrsc[i+1][1]] ,[intrsc[i][2], intrsc[i+1][2]] )

	
	#plt.plot([intrsc[i][0], intrsc[i+1][0]],[intrsc[i][1], intrsc[i+1][1]] )
plt.show()

#file.close()


