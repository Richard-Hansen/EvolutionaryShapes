import sys, random
import pygame
from pygame.locals import *
import pymunk
import pymunk.pygame_util

from Overlord import Overlord

def start_simulation():
	pygame.init()
	display_x = 700
	display_y = 600
	screen = pygame.display.set_mode((display_x, display_y))
	pygame.display.set_caption("Fitness Test")

	space = pymunk.Space()
	space.gravity = (0.0, -900.0)

	draw_options = pymunk.pygame_util.DrawOptions(screen)

	# Overlord watches over all creatures and obstacles, and handles updates
	eps = 0.1 # mutation rate
	OVR = Overlord(screen, space, draw_options, display_x, display_y, eps)

	# simulation loop
	while True:

		# Check to see if the user has exited the game
	    for event in pygame.event.get():
	        if event.type == QUIT:
	            sys.exit(0)
	        elif event.type == KEYDOWN and event.key == K_ESCAPE:
	            sys.exit(0)

	    # Overlord update
	    OVR.update()

if __name__ == '__main__':
    start_simulation()



