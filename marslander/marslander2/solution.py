#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import math
import random
import numpy as np
from enum import Enum
from copy import deepcopy

POWER_MIN = 0
POWER_MAX = 4
POWER_LIMIT = 1
ROTATION_MIN = -90
ROTATION_MAX = 90
ROTATION_LIMIT = 15
GRAVITY = np.array([0, -3.711])
WIDTH_MAX = 7000
HEIGHT_MAX = 3000

CHROMOSOME_SIZE = 100
POPULATION_SIZE = 20
GENERATION_COUNT = 100
MUTATION_CHANCE = 0.01
ELITISM = True


class FlyState(Enum):
    LANDED = 0
    FLYING = 1
    CRASHED = 2
    LOST = 3


class State:
    def __init__(self):
        self.step = 1
        self.position = [0, 0]
        self.velocity = [0, 0]
        self.fuel = 0
        self.angle = 0
        self.power = 0
        self.fly_state = FlyState.CRASHED


def trim(value, limit):
    if value < -limit:
        return -limit
    elif value > limit:
        return limit
    else:
        return value


def rotate_vector(vector, angle):
    radians = math.radians(angle)
    result = [None] * 2
    result[0] = (vector[0] * math.cos(radians) - vector[1] * math.sin(radians)) * -1
    result[1] = vector[0] * math.sin(radians) + vector[1] * math.cos(radians)
    return np.array(result)


def calculate_trajectory(x, y, h_speed, v_speed, fuel, rotate, power, landing_zone, chromosome):
    state = State()
    state.step = 1
    state.position = [x, y]
    state.velocity = [h_speed, v_speed]
    state.fuel = fuel
    state.angle = rotate
    state.power = power
    state.fly_state = FlyState.FLYING

    states = [state]
    for gene in chromosome:
        new_state = deepcopy(state)

        new_state.angle += trim(gene[0] - state.angle, ROTATION_LIMIT)
        new_state.power += trim(gene[1] - state.power, POWER_LIMIT)
        new_state.fuel -= new_state.power
        thrust = rotate_vector(np.array([0., 1.]) * new_state.power, new_state.angle)
        if new_state.fuel <= 0:
            thrust = 0
        new_state.velocity += GRAVITY + thrust
        new_state.position += new_state.velocity
        new_state.step += 1
        new_state.fly_state = FlyState.FLYING

        if new_state.position[0] < 0 or new_state.position[0] > WIDTH_MAX or new_state.position[1] > HEIGHT_MAX:
            new_state.fly_state = FlyState.LOST
        #elif new_state.position < landing_zone[1]:
        elif (landing_zone[0][0] <= new_state.position[0] <= landing_zone[1][0] and
             landing_zone[0][1] >= new_state.position[1]):
            speed = np.linalg.norm(new_state.velocity)
            new_state.fly_state = FlyState.LANDED if speed > 30 else FlyState.CRASHED
        elif (new_state.position[1] < landing_zone[0][1]):
            new_state.fly_state = FlyState.CRASHED

        states.append(new_state)

        if new_state.fly_state != FlyState.FLYING:
            break

        state = new_state

    return states


def fitness(x, y, h_speed, v_speed, fuel, rotate, power, landing_zone, chromosome):
    result = None
    trajectory = calculate_trajectory(x, y, h_speed, v_speed, fuel, rotate, power, landing_zone, chromosome)

    print(trajectory, file=sys.stderr)

    last_state = trajectory[-1]
    if last_state[5] == FlyState.LANDED:
        result = last_state[3]
    elif last_state[5] == FlyState.FLYING:
        # result = 1-((last_state[1] - landing_height)/3000)
        result = 0.5
    elif last_state[1] > HEIGHT_MAX:
        result = 0
    else:
        result = 200 / -last_state[2]

    '''
    print('y:{} s:{} f:{} = {}'.format(int(last_state[1]), int(last_state[2]), int(last_state[3]), int(result)),
          file=sys.stderr)
    '''
    return result


def random_population():
    population = []
    for i in range(POPULATION_SIZE):
        chromosome = []
        for j in range(CHROMOSOME_SIZE):
            rotation = (random.randint(1, 13) - 7) * 15
            power = random.randint(POWER_MIN, POWER_MAX)
            chromosome.append((rotation, power))

        population.append(chromosome)
    return population


def get_best_trajectory(x, y, h_speed, v_speed, fuel, rotate, power, landing_zone):
    population = random_population()
    for generation_idx in range(GENERATION_COUNT):
        weighted_population = []
        fitness_array = []
        for chromosome in population:
            fitness_value = fitness(x, y, h_speed, v_speed, fuel, rotate, power, landing_zone, chromosome)
            fitness_array.append(fitness_value)
            weighted_population.append((chromosome, fitness_value))

        text = '{:02d}\t'.format(generation_idx + 1)
        text += ' '.join([format(int(item), '>3d') for item in fitness_array])
        text += ' = {}'.format(int(sum(fitness_array)))
        print(text, file=sys.stderr)

        population = []

        inherit_population_count = POPULATION_SIZE//2
        if ELITISM:
            inherit_population_count -= 1
            elites = sorted(weighted_population, key=lambda item: item[1], reverse=True)[:2]
            population = [item[0] for item in elites]

        '''
        for _ in range(inherit_population_count):
            chromosome1 = weighted_choice(weighted_population)
            chromosome2 = weighted_choice(weighted_population)

            chromosome1, chromosome2 = crossover(chromosome1, chromosome2)

            population.append(mutate(chromosome1))
            population.append(mutate(chromosome2))
        '''

    best_chromosome = population[0]
    best_fitness = fitness(x, y, h_speed, v_speed, fuel, rotate, power, landing_zone, chromosome)
    for chromosome in population:
        fitness_value = fitness(x, y, h_speed, v_speed, fuel, rotate, power, landing_zone, chromosome)
        if fitness_value > best_fitness:
            best_chromosome = chromosome
            best_fitness = fitness_value

    '''
    found = calculate_trajectory(landing_height, position, speed, fuel, power, best_chromosome)

    print('Best solution:', file=sys.stderr)
    print('chromosome: ' + str(decode_chromosome(best_chromosome)), file=sys.stderr)
    print('fitness: ' + str(best_fitness), file=sys.stderr)
    print('last state: ' + str(found[-1]), file=sys.stderr)

    return found
    '''
    return None


def get_surface():
    surface = []
    surface_n = int(input())
    for i in range(surface_n):
        land_x, land_y = [int(j) for j in input().split()]
        surface.append((land_x, land_y))
    # print(surface, file=sys.stderr)
    return surface


def calculate_landing_zone():
    landing_zone = [None] * 2
    for point1, point2 in zip(surface, surface[1:]):
        if point1[1] == point2[1]:
            landing_zone[0] = point1
            landing_zone[1] = point2
    return landing_zone


if __name__ == "__main__":
    surface = []
    landing_zone = []
    best_trajectory = None

    surface = get_surface()
    landing_zone = calculate_landing_zone()

    while True:
        x, y, h_speed, v_speed, fuel, rotate, power = [int(i) for i in input().split()]

        if best_trajectory is None:
            best_trajectory = get_best_trajectory(x, y, h_speed, v_speed, fuel, rotate, power, landing_zone)

        if len(best_trajectory) > 0:
            cmd = best_trajectory.pop(0)[4]
            print('0 {}'.format(cmd))
        else:
            print("30 2")   # rotate power
