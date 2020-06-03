import sys, random
import pygame
from pygame.locals import *
import pymunk
import pymunk.pygame_util

from Obstacle import Obstacle
from Creature import Creature

# handles game functionality, including colision and evolution management
class Overlord:
	def __init__(self, screen, space, draw_options, display_x, display_y, epsilon, population_size=10, simulation_step=0.1, epochs=1000):

		# screen we are drawing on
		self.screen = screen

		# simulation space
		self.space = space

		# used for easy drawing of all simulation objects
		self.draw_options = draw_options

		# width and height of the screen for the fitness test and side bar
		self.fitness_display_x, self.fitness_display_y = 0.9*display_x, display_y
		self.sidebar_display_x, self.sidebar_display_y = 0.1*display_x, display_y
		self.sidebar_display_start_x = self.fitness_display_x

		#the zone in which creatures can be instantiated
		self.creation_bounds = self.make_creation_bounds() 

		# all living creatures
		self.population_size = population_size

		# the number of steps in the simulation we advance after each iteration
		self.simulation_step = simulation_step

		# populate creatures
		self.creatures = []
		for i in range(self.population_size):
			c = Creature(self.creation_bounds)
			# c.build_creature(self.space)
			self.creatures.append(c)

		# sidebar creatures
		self.sidebar_creatures = self.populate_sidebar()

		# mutation rate for creatures
		self.epsilon = epsilon

		# all static obstacles
		self.obstacles = self.obstacle_set_1()

		# variables used for each generation, this includes fitness scores and current creatures indices
		self.epoch = 0
		self.current_creature_ind = 0
		self.fitness_scores = [None for x in range(self.population_size)]

	# builds the zone in which creatures can be instantiated
	def make_creation_bounds(self):
		return [0.05*self.fitness_display_x, 0.95*self.fitness_display_x, 0.9*self.fitness_display_y, self.fitness_display_y]

	# displays all the creatures in the population as static objects in the sidebar
	def populate_sidebar(self, refresh=False):

		if refresh:
			self.clear_sidebar()

		# calculate the starting x position and the separation between each sidebar object on the y axis
		creature_separation = (0.9*self.sidebar_display_y) / max(1,len(self.creatures))
		x = self.sidebar_display_start_x + self.sidebar_display_x / 2

		# list of objects in the sidebar
		sidebar_creatures = []

		# make each creature as a static object in the sidebar
		count = 1
		for c in self.creatures:
			ob = Obstacle(c.vertices, (x,self.sidebar_display_y - creature_separation*count), self.space)
			sidebar_creatures.append(ob)
			count += 1

		return sidebar_creatures

	# removes all objects in the sidebar
	def clear_sidebar(self):
		for ob in self.sidebar_creatures:
			self.space.remove(ob.shape,ob.shape.body)

	# test a creature in the population
	#TODO: update the population
	def test_creatures(self):

		current_creature = self.creatures[self.current_creature_ind]

		if current_creature.shape == None:
			current_creature.build_creature(self.space)

		if not current_creature.in_space:
			current_creature.add_to_space(self.space)

		# update the creature's lowest y-value and time of making it there.
		# if the creature is greater than or equal to the specified species age,
		# this constitutes a completed life_cycle, which will be a value of either
		# 1 or 0. When a life cycle is completed, the creature dies and score is recorded
		life_cycle = current_creature.update(self.simulation_step)

		# if life cycle is complete (== 1), record best scores for the creature and select the next creature
		# if 
		if life_cycle == 1:
			self.fitness_scores[self.current_creature_ind] = (current_creature.lowest_y, current_creature.time_of_low_point)
			self.remove_creature_from_space(current_creature)
			self.current_creature_ind += 1

			if self.current_creature_ind >= self.population_size:
				self.update_population()
				self.epoch += 1

			


	def update_population(self):
		#self.print_population_scores()

		zip_list = zip(self.fitness_scores,self.creatures)

		# calculate 2 best and 1 worst member of the population
		sorted_scores = []
		for i in range(self.population_size):
			fitness_rating = self.calculate_fitness_rating(self.fitness_scores[i])
			sorted_scores.append((fitness_rating,self.creatures[i]))

		# sort scores by fitness rating in descending order
		sorted_scores.sort(key=lambda t:t[0],reverse=True)

		#print("Current pop: " + str(self.creatures))
		# delete worst 2 members
		sorted_scores.pop()
		sorted_scores.pop()

		# breed 2 best and add child to population
		p1 = sorted_scores[0][1]
		p2 = sorted_scores[1][1]
		new_creature = Creature(self.creation_bounds,[p1,p2],self.epsilon)
		self.creatures = [new_creature]
		#print(len(sorted_scores))
		for v in sorted_scores:
			self.creatures.append(v[1])

		# add a completely random member to the population
		self.creatures.append(Creature(self.creation_bounds))

		#print("New pop: " + str(self.creatures))

		# repopulate sidebar with new population
		self.sidebar_creatures = self.populate_sidebar(refresh=True)

		#reset all creature metadta
		for c in self.creatures:
			c.reset()

		#reset current creature index for next iteration
		self.current_creature_ind = 0

	# given a tuple of a creature's fitness scores, calculate an arbitrary rating value of the performance
	def calculate_fitness_rating(self,tup):
		return 1 / tup[0]
	
	def print_population_scores(self):
		print("########## Epoch: {} ##########".format(self.epoch))
		for i in range(self.population_size):
			print("Creature: {}".format(i))
			print("\t Lowest point: {}".format(self.fitness_scores[i][0]))
			print("\t Time:         {}\n".format(self.fitness_scores[i][1]))


	# remove the specified creature from the game space.
	def remove_creature_from_space(self, creature):
		self.space.remove(creature.shape,creature.shape.body)
		creature.in_space = 0


	def update(self):
		# wipe the screen
		self.screen.fill((255,255,255))

		# p1 = random.choice(self.creatures)
		# p2 = random.choice(self.creatures)
		# c = Creature(self.creation_bounds, parents=(p1, p2))
		# c.build_creature(self.space)

		# test a creature. Once a creature has completed testing, the next creature will be tested.
		# after all creatures have been tested, the epoch ends, the population is updated, and we repeat
		self.test_creatures()
		

		# draw all objects attatched to the space
		self.space.debug_draw(self.draw_options)

		# increment the simulation by one step
		for i in range(1000):
			self.space.step(self.simulation_step/10.0)

		# set the display to the current buffered display
		pygame.display.flip()

	def obstacle_set_1(self):

		lw_p = (0,0)
		lw_v = [(0, 0), (0.01*self.fitness_display_x,0), (0.01*self.fitness_display_x, self.fitness_display_y), (0, self.fitness_display_y)]
		lw = Obstacle(lw_v, lw_p, space=self.space)

		rw_p = (0.99*self.fitness_display_x,0)
		rw_v = [(0, 0), (0.01*self.fitness_display_x,0), (0.01*self.fitness_display_x, self.fitness_display_y), (0, self.fitness_display_y)]
		rw = Obstacle(rw_v, rw_p, space=self.space)

		bot_p = (0,0)
		bot_v = [(0,0),(self.fitness_display_x, 0), (self.fitness_display_x,0.01*self.fitness_display_y), (0, 0.01*self.fitness_display_y)]
		bot = Obstacle(bot_v, bot_p, space = self.space)

		p1 = (0.5*self.fitness_display_x,0)
		v1 = [(0,0.8*self.fitness_display_y),(0,0.7*self.fitness_display_y), (0.5*self.fitness_display_x,0.7*self.fitness_display_y)]
		ob1 = Obstacle(v1,p1,space=self.space)

		p2 = (0.5*self.fitness_display_x,0)
		v2 = [(0,0.8*self.fitness_display_y),(0,0.7*self.fitness_display_y), (-0.3*self.fitness_display_x,0.7*self.fitness_display_y)]
		ob2 = Obstacle(v2,p2,space=self.space)

		p3 = (0,0)
		v3 = [(0,0.7*self.fitness_display_y),(0,0.55*self.fitness_display_y), (0.8*self.fitness_display_x,0.565*self.fitness_display_y), (0.8*self.fitness_display_x,0.57*self.fitness_display_y)]
		ob3 = Obstacle(v3,p3,space=self.space)

		p4 = (0.5*self.fitness_display_x,0)
		v4 = [(0.5*self.fitness_display_x,0.54*self.fitness_display_y),(0.5*self.fitness_display_x,0.45*self.fitness_display_y), (-0.4*self.fitness_display_x,0.40*self.fitness_display_y)]
		ob4 = Obstacle(v4,p4,space=self.space)

		return [lw, rw, bot, ob1, ob2, ob3, ob4]
