#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import math
import random
from enum import Enum

'''
power: 0-4 -> 0 1 2 3 4 	-> 5 values     -> 5 DEC = 101 BIN
time: 1-40 -> 1 2 .. 39 40	-> 40 values    -> 40 DEC = 101000 BIN
chromosome: 3 + 6 = 9 bits for one command
'''

POWER_MIN = 0
POWER_MAX = 4
POWER_SIZE = int(math.log2(POWER_MAX)) + 1
POWER_LIMIT = 1
TIME_MIN = 5
TIME_MAX = 20
TIME_SIZE = int(math.log2(TIME_MAX)) + 1
GRAVITY = -3.711
HEIGHT_MAX = 3000


COMMAND_SIZE = POWER_SIZE + TIME_SIZE
COMMAND_COUNT = 10
CHROMOSOME_SIZE = COMMAND_SIZE * COMMAND_COUNT
POPULATION_SIZE = 20
GENERATION_COUNT = 20

MUTATION_CHANCE = 0.01


class FlyState(Enum):
    LANDED = 0
    FLYING = 1
    CRASHED = 2


def encode_chromosome(commands):
    chromosome = ''
    for command in commands:
        chromosome += format(command[0], '03b') + format(command[1], '06b')
    return chromosome


def replace_command(chromosome, command_idx, command):
    command_start = command_idx * COMMAND_SIZE
    encoded_command = format(command[0], '03b') + format(command[1], '06b')
    command_end = command_start + COMMAND_SIZE
    return chromosome[:command_start] + encoded_command + chromosome[command_end:]


def decode_chromosome_idx(chromosome, command_idx):
    command_start = command_idx * COMMAND_SIZE
    power = int(chromosome[command_start:command_start + POWER_SIZE], 2)
    time = int(chromosome[command_start + POWER_SIZE:command_start + POWER_SIZE + TIME_SIZE], 2)
    return power, time


def decode_chromosome(chromosome):
    commands = []
    for command_idx in range(COMMAND_COUNT):
        power, time = decode_chromosome_idx(chromosome, command_idx)
        commands.append((power, time))
    return commands


def trim(value, limit):
    if value < -limit:
        return -limit
    elif value > limit:
        return limit
    else:
        return value


def calculate_trajectory(landing_height, initial_position, initial_speed, initial_fuel, initial_power, chromosome):
    time = 1
    position = initial_position
    speed = initial_speed
    fuel = initial_fuel
    power = initial_power
    fly_state = FlyState.FLYING

    states = [[time, position, speed, fuel, power, FlyState.FLYING]]
    for command in decode_chromosome(chromosome):
        cmd_power = command[0]
        cmd_time = command[1]

        for _ in range(cmd_time):
            power += trim(cmd_power - power, POWER_LIMIT)
            speed += GRAVITY + power
            position += speed
            fuel -= power
            time += 1

            if position > HEIGHT_MAX:
                fly_state = FlyState.CRASHED
            elif position < landing_height:
                fly_state = FlyState.LANDED if speed > -40 else FlyState.CRASHED

            states.append([time, position, speed, fuel, power, fly_state])

            if fly_state != FlyState.FLYING:
                break

        if fly_state != FlyState.FLYING:
            break

    return states


def weighted_choice(pairs):
    weight_total = sum((item[1] for item in pairs))
    n = random.uniform(0, weight_total)
    for item, weight in pairs:
        if n < weight:
            return item
        n = n - weight
    return item


def random_population():
    population = []
    for chromosome_idx in range(POPULATION_SIZE):
        commands = []
        for command_idx in range(COMMAND_COUNT):
            power = random.randint(POWER_MIN, POWER_MAX)
            time = random.randint(TIME_MIN, TIME_MAX)
            commands.append((power, time))

        population.append(encode_chromosome(commands))
    return population


def fitness(landing_height, position, speed, fuel, power, chromosome):
    result = None
    trajectory = calculate_trajectory(landing_height, position, speed, fuel, power, chromosome)
    last_state = trajectory[-1]
    if last_state[5] == FlyState.LANDED:
        result = last_state[3]
    elif last_state[5] == FlyState.FLYING:
        # result = - last_state[1] + landing_height
        result = 1-((last_state[1]-landing_height)/3000)
    elif last_state[1] > HEIGHT_MAX:
        result = 0
    else:
        result = 200 / -last_state[2]

    '''
    print('y:{} s:{} f:{} = {}'.format(int(last_state[1]), int(last_state[2]), int(last_state[3]), int(result)),
          file=sys.stderr)
    '''
    return result


def crossover(chromosome1, chromosome2):
    pos = int(random.random() * COMMAND_COUNT) * COMMAND_SIZE
    return chromosome1[:pos] + chromosome2[pos:], chromosome2[:pos] + chromosome1[pos:]


def mutate(chromosome):
    mutated = chromosome
    mutations = int(MUTATION_CHANCE * CHROMOSOME_SIZE) + 1
    for _ in range(mutations):
        if random.randrange(MUTATION_CHANCE * 100) == 0:
            command_idx = random.randrange(COMMAND_COUNT)
            power, time = decode_chromosome_idx(mutated, command_idx)
            if random.randrange(COMMAND_SIZE) < POWER_SIZE:
                power = random.randint(POWER_MIN, POWER_MAX)
            else:
                time = random.randint(TIME_MIN, TIME_MAX)
            mutated = replace_command(mutated, command_idx, (power, time))

    return mutated


def get_best_trajectory(landing_height, position, speed, fuel, power):
    population = random_population()
    for generation_idx in range(GENERATION_COUNT):
        #print('Gen:{} Pop:{}'.format(generation_idx, population[0]), file=sys.stderr)
        weighted_population = []

        fitness_array = []
        for chromosome in population:
            fitness_value = fitness(landing_height, position, speed, fuel, power, chromosome)
            fitness_array.append(fitness_value)
            weighted_population.append((chromosome, fitness_value))

        text = '{:02d}\t'.format(generation_idx + 1)
        text += ' '.join([format(int(item), '>3d') for item in fitness_array])
        text += ' = {}'.format(int(sum(fitness_array)))
        print(text, file=sys.stderr)

        population = []

        for _ in range(POPULATION_SIZE//2):
            chromosome1 = weighted_choice(weighted_population)
            chromosome2 = weighted_choice(weighted_population)

            chromosome1, chromosome2 = crossover(chromosome1, chromosome2)

            population.append(mutate(chromosome1))
            population.append(mutate(chromosome2))

    best_chromosome = population[0]
    best_fitness = fitness(landing_height, position, speed, fuel, power, best_chromosome)
    for chromosome in population:
        fitness_value = fitness(landing_height, position, speed, fuel, power, chromosome)
        if fitness_value > best_fitness:
            best_chromosome = chromosome
            best_fitness = fitness_value

    found = calculate_trajectory(landing_height, position, speed, fuel, power, best_chromosome)

    print('Best solution:', file=sys.stderr)
    print('chromosome: ' + str(decode_chromosome(best_chromosome)), file=sys.stderr)
    print('fitness: ' + str(best_fitness), file=sys.stderr)
    print('last state: ' + str(found[-1]), file=sys.stderr)

    return found


if __name__ == "__main__":
    surface_n = int(input())
    surface = []
    for i in range(surface_n):
        land_x, land_y = [int(j) for j in input().split()]
        surface.append(land_y)

    # find the landing zone (height only for now)
    landing_zone = 0
    for point1, point2 in zip(surface, surface[1:]):
        if point1 == point2:
            landing_zone = point1

    # To debug: print("Debug messages...", file=sys.stderr)

    best_trajectory = None
    while True:
        x, y, h_speed, v_speed, actual_fuel, rotate, actual_power = [int(i) for i in input().split()]

        if best_trajectory is None:
            best_trajectory = get_best_trajectory(landing_zone, y, v_speed, actual_fuel, actual_power)

        if len(best_trajectory) > 0:
            cmd = best_trajectory.pop(0)[4]
            print('0 {}'.format(cmd))
        else:
            print('0 0')
