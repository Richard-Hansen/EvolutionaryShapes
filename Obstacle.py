import random
import pymunk

class Obstacle:
	def __init__(self, vertices, position, space=None):

		# vertices of the obstacle
		self.vertices = vertices

		# position of the obstacles
		self.position = position

		# if a space to build the object is provided, build the obstacle within the space
		if space != None:
			self.shape = self.build_obstacle(space)

	# builds a static body which creatures will collide with
	def build_obstacle(self, space):
		body = pymunk.Body(body_type = pymunk.Body.STATIC)
		body.position = self.position[0], self.position[1]
		shape = pymunk.Poly(body, self.vertices)
		shape.friction = 0.6
		space.add(body, shape)
		return shape

