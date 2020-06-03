import random
import pymunk
import math

class Creature:
	def __init__(self, creation_bounds, parents=None, epsilon=0.05, max_magnitude=20, max_coords=50, friction=0.2, species_age = 1):

		# the creation bounds defines where the creature can be made/spawn
		# in the form [x_min,x_max,y_min,y_max]
		self.creation_bounds = creation_bounds

		# maximum r value for polar coordinates
		self.max_magnitude = max_magnitude

		# friction value of the shape. 0 is frictionless
		self.friction = friction

		# if we are creating a random shape, generate random polar coordiantes
		if parents == None:
			# starting position of the creature
			x = random.uniform(self.creation_bounds[0],self.creation_bounds[1])
			y = random.uniform(self.creation_bounds[2],self.creation_bounds[3])
			self.pos = (x,y)

			#polar coordinates, sorted by increasing degrees from the x axis (1st quadrant based)
			self.polar_coordinates = self.__generate_random_polar_coordinates(max_coords)
		else:
			self.pos, self.polar_coordinates = self.__breed_parents(parents[0],parents[1],epsilon)

		#self.polar_coordinates = [(8,0),(8,45),(8,90),(8,135),(8,180),(8,225),(8,270),(8,315)]

		# calculate the shape's vertices given the polar coordinates
		self.vertices = self.__polar_coordinates_to_vertices()

		# variables for scoring creature during fitness test
		self.lowest_y = self.pos[1]
		self.time_of_low_point = 0
		self.age = 0
		self.species_age = species_age

		# pymunk polygon object. set to 1 if the creature is in the game space
		self.in_space = 0

		self.shape = None
		self.collision_layer = 1
		#self.shape = self.build_creature(space) 

	# sets all creature values back to defaults
	def reset(self):
		self.lowest_y = self.pos[1]
		self.time_of_low_point = 0
		self.age = 0
		self.in_space = 0

		if self.shape != None:
			self.shape.body.position = self.pos

	# builds a creature within set creation bounds. 
	def build_creature(self, space):
		mass = 1
		inertia = pymunk.moment_for_poly(mass, self.vertices)
		print("Inertia: {0}".format(inertia))
		if not inertia > 0:
			self.__debug_message()
			raise ValueError("Creature: Moment of intertia is less than 0")
			return

		body = pymunk.Body(mass, inertia)
		body.position = self.pos
		shape = pymunk.Poly(body, self.vertices)
		shape.friction = 0.2
		space.add(body, shape)
		print("creature created successfully")
		print("###")
		self.shape = shape
		self.in_space = 1
		self.set_collision_layer()
		return shape

	# sets the collision error for the creature
	def set_collision_layer(self, layer = 1):
		self.collision_layer = layer

	# build this creature provided with two parents and a mutation rate
	def __breed_parents(self, c1, c2, epsilon):
		#print("###")

		# starting position ranges
		starting_pos_x_range = (min(c1.pos[0],c2.pos[0]),max(c1.pos[0],c2.pos[0]))
		starting_pos_y_range = (min(c1.pos[1],c2.pos[1]),max(c1.pos[1],c2.pos[1]))

		# choose a position within the parent's starting range, or mutate to a new random position
		e = random.uniform(0,1)
		if e < epsilon:
			new_pos = self.__mutate_position()
		else:
			new_pos = (random.uniform(starting_pos_x_range[0],starting_pos_x_range[1]), random.uniform(starting_pos_y_range[0],starting_pos_y_range[1]))

		# range of vertex count
		lower_vertex_count = min(len(c1.vertices), len(c2.vertices))
		upper_vertex_count = max(len(c1.vertices), len(c2.vertices))

		# if we successfully mutate the vertex count, increase the range of possible vertex choices by 
		# decreasing the lower bound by 1 (min of 3) and increasing the upper bound by 1
		e = random.uniform(0,1)
		if e < epsilon:
			vertex_range = (3, lower_vertex_count+upper_vertex_count)
		else:
			vertex_range = (lower_vertex_count, upper_vertex_count)

		# pick a vertex count
		#print(vertex_range)
		new_num_vertices = random.randint(lower_vertex_count,upper_vertex_count)
		#print(new_num_vertices)
		# creature polygon including all vertices from both parents. Then, continually merge
		# the two closest points until we have reached the new_num_vertices count.
		combined_polar_coordinates = c1.polar_coordinates + c2.polar_coordinates
		combined_polar_coordinates.sort(key = lambda tup: tup[1])

		unmutated_polar_coordinates = self.__prune_merge_polar_coordinates(combined_polar_coordinates, new_num_vertices)

		# mutate vertices, adding random ones if there is a mutation, otherwise adding the 
		# coordinates present in unmutated_polar_coordinates
		new_polar_coordinates = []
		for i in range(len(unmutated_polar_coordinates)):
			e = random.uniform(0,1)
			if e < epsilon:
				p = self.__mutate_polar_coordinate()
				while p in new_polar_coordinates:
					p = self.__mutate_polar_coordinate()
				new_polar_coordinates.append(p)
			else:
				new_polar_coordinates.append(unmutated_polar_coordinates[i])

		new_polar_coordinates.sort(key=lambda tup: tup[1])
		return new_pos, new_polar_coordinates

	# given a list of polar coordinates remove closest coordinates and replace with average until
	# the length of coords is equal to count
	def __prune_merge_polar_coordinates(self, coords, count):
		# create a list of all distances
		dist_list = []
		for i in range(0, len(coords)):
			for j in range(i, len(coords)):
				dist = self.__polar_coordinate_distance(coords[i],coords[j])
				dist_list.append((dist, coords[i], coords[j]))

		# sort by distance
		dist_list.sort(key=lambda tup: tup[0])

		while len(coords) > count:
			#print("Closest: {0} {0}".format(dist_list[1],dist_list[2]))
			# average the magnitude and degrees to create a new polar coordinate
			new_coord = ((dist_list[0][1][0] + dist_list[0][2][0]) / 2.00, (dist_list[0][1][1] + dist_list[0][2][1]) / 2.00)

			# store tuples in variable for readability
			tup_1 = dist_list[0][1]
			tup_2 = dist_list[0][2]

			# remove choice from list of coordinates
			coords = [c for c in coords if c != tup_1 and c != tup_2]

			# add new coordinate to list of coordinates
			coords.append(new_coord)

			#print(len(dist_list))
			# remove all distances that used the merged coordinates
			dist_list = [v for v in dist_list if v[1] != tup_1 and v[1] != tup_2 and v[2] != tup_1 and v[2] != tup_2]
			

			# calculate distance from new_coord to all other coordinates and insert in order
			for i in range(len(coords)-1):
				dist = self.__polar_coordinate_distance(coords[i], coords[len(coords)-1])
				dist_list.append((dist, coords[i],coords[len(coords)-1]))
			#print(len(dist_list))

			# sort by distance
			dist_list.sort(key=lambda tup: tup[0])

		#print(len(coords),count)
		#print(coords)
		return coords

	# calculates the distance between 2 polar coordinates
	def __polar_coordinate_distance(self,pc1,pc2):
		return (pc1[0]**2 + pc2[0]**2 - 2*pc1[0]*pc2[0]*math.cos(math.radians(pc1[1] - pc2[1])))**(0.5)

	# returns a new position mutated from the original 2 positions
	def __mutate_position(self):
		# starting position of the creature
		x = random.uniform(self.creation_bounds[0],self.creation_bounds[1])
		y = random.uniform(self.creation_bounds[2],self.creation_bounds[3])
		return (x,y)

	# returns a new random polar coordinate
	def __mutate_polar_coordinate(self):
		# generate and return a single polar coordinate
		return self.__generate_random_polar_coordinates(1, min_coords=1)[0]


	# generates random polar coordinates between min_coords (default 3) and max_coords, with a magnitude for each polar coordinate
	# between 1 and max_magnitude
	def __generate_random_polar_coordinates(self,max_coords,min_coords=3):

		#return [(10,45),(10,135),(10,225),(10,315)]

		# randomly select a number of coordinates for the shape
		num_coordinates = random.randint(min_coords,(max(min_coords, max_coords)))

		# list of polar coordinates and degrees used
		polar_coordinates = []
		degree_list = []

		# create the random coordinates
		counter = num_coordinates
		while counter > 0:
			r = random.randint(1, self.max_magnitude)
			theta = random.randint(0,360)

			# ensure we do not have 2 coordinates with the same degree
			if theta not in degree_list:
				polar_coordinates.append((r,theta))
				degree_list.append(theta)
				counter -= 1

		polar_coordinates.sort(key=lambda tup: tup[1])
		return polar_coordinates

	# converts polar coordinates to vertices
	def __polar_coordinates_to_vertices(self):

		vertices = []

		for pc in self.polar_coordinates:
			vertices.append((pc[0] * math.cos(math.radians(pc[1])),pc[0] * math.sin(math.radians(pc[1]))))

		return vertices

	# simple debug details
	def __debug_message(self):
		print("##### This creature caused an error #####")

		print("Polar Coordinates")
		for pc in self.polar_coordinates:
			print("\t {0}".format(pc))

		print("Vertices")
		for v in self.vertices:
			print("\t {0}".format(v))

		print("#########################################")

	# add creature to space
	def add_to_space(self, space):
		space.add(self.shape.body, self.shape)
		self.in_space = 1

	# returns magnitude of a vector
	def mag(self,v):
		return (v[0]**2 + v[1]**2)**(1/2.00)

	# Update function, modifies creature's score depending on it's performance after a certain number of simulation steps
	def update(self, simulation_steps):
		curr_lowest_y = self.creation_bounds[3] # the highest y value that a shape can be at
		
		for v in self.shape.get_vertices():
			x,y = v.rotated(self.shape.body.angle) + self.shape.body.position
			curr_lowest_y = min(curr_lowest_y, y)

		#print(self.shape.body.velocity)
		if curr_lowest_y < self.lowest_y:
			self.lowest_y = curr_lowest_y
			self.time_of_low_point = self.age


		# if the shape is a certain age and has a very low velocity, kill it
		# if self.age > self.species_age / 5.00 and self.mag(self.shape.body.velocity) < 0.01:
		# 	return 1

		self.age += simulation_steps

		# if the shape has 'lived' for the lifetime of the species
		if self.age >= self.species_age:
			return 1

		

		return 0



