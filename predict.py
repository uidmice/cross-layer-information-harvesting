import numpy as np
import matplotlib.pyplot as plt
import itertools
from Simulation import Simulation
from framework.Environment import Environment
from framework.utils import load_config, random_policy, load_field
from setup import *
import pickle
from framework.Gateway import  Gateway

DEBUG = False

num_steps = 1000
step_time = 2500  # ms
offset = 1000
config = 'simple1'

node_locations, gateway_locations, info_group, collision_group = load_config(config)
field_para = load_field(config)
simulation = Simulation(node_locations, gateway_locations, info_group, collision_group, step_time, Environment(field_para), num_steps, offset=offset)

repeat = 5
random_para = np.arange(0.05, 0.5, 0.05)

for j, prob in enumerate(random_para):
    print("Probability: "+ str(prob))
    for i in range(repeat):
        print('\t ' + str(i))
        simulation.reset()
        for k in range(num_steps):
            send, success = simulation.step(random_policy(prob, simulation))
            print("Node "+str(send) + ' sent')
            print("Node " + str(success) + ' success')
            print('True field\t'+ str(simulation.temp_field))
            print('Recorded field\t' + str(simulation.constructed_field))