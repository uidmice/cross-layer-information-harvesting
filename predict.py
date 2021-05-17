import numpy as np
import matplotlib.pyplot as plt
import itertools
from Simulation import Simulation
from framework.utils import load_config, random_policy, field_construct_data, random_network_construct, play_field_video, fixed_policy
from config import *
import pickle
from framework.Gateway import  Gateway

DEBUG = False

num_steps = 1000
step_time = 6000  # ms
offset = 1000
fire_update = 6000
config = 'random1'

gateway_location, node_locations, connection, distance = load_config(config)
simulation = Simulation(node_locations, gateway_location, step_time, connection, config, distance, num_steps, offset=offset, update_rate=fire_update)

# dT = np.diff(simulation.environment.T_field, axis=0)
# print(np.max(dT))
#
policy_random = lambda x: random_policy(0.5, x)
policy_random.name = "random_0.5"

policy_fixed = lambda x: fixed_policy(5,2, x)
policy_fixed.name = 'fixed_2_5'
# field_construct_data(simulation, num_steps, step_time/1000, policy_fixed, scale=100, show=True)
# random_network_construct(simulation, num_steps, policy_fixed)


repeat = 5
random_para = np.arange(0.05, 0.5, 0.05)
PER_random = np.zeros((len(random_para), repeat, num_steps))
pos_reward_random = np.zeros((len(random_para), repeat, num_steps, len(node_locations)))
success_nodes = np.zeros((len(random_para), repeat, num_steps, len(node_locations)))
send_nodes = np.zeros((len(random_para), repeat, num_steps, len(node_locations)))
real_field = np.zeros((len(random_para), repeat, num_steps, len(node_locations)))
constructed_field = np.zeros((len(random_para), repeat, num_steps, len(node_locations)))

temp_field = np.zeros((num_steps, 2* distance//GRID + 1, 2* distance//GRID + 1))

for i in range(num_steps):
    temp_field[i, :, :] = simulation.environment.T_field[i*step_time//fire_update]

for j, prob in enumerate(random_para):
    print("Probability: "+ str(prob))
    for i in range(repeat):
        print('\t ' + str(i))
        simulation.reset()
        for k in range(num_steps):
            send, success = simulation.step(random_policy(prob, simulation))
            success_array = np.zeros(len(node_locations))
            send_array = np.zeros(len(node_locations))
            success_array[success] = 1
            send_array[send] = 1

            success_nodes[j, i, k, :] = success_array
            send_nodes[j,i,k,:] = send_array

            real_field[j, i, k, :] = np.fromiter(simulation.real_field.values(), dtype=float)
            constructed_field[j, i, k, :] = np.fromiter(simulation.constructed_field.values(), dtype=float)
            pos_reward = np.absolute(real_field[j, i, k, :] - constructed_field[j, i, k, :])

            pos_reward_random[j,i,k,:] = pos_reward * success_array
            n = max(len(send), 1)
            PER_random[j, i, k] = len(success) / n

name = "result/"+ config +"/no_channel_" + str(Gateway.NO_CHANNELS) +"/offset_"+str(offset) +"/update_" + str(fire_update) +"_random_full1.pickle"

pickle.dump([PER_random, pos_reward_random, send_nodes, success_nodes, real_field, constructed_field, temp_field], open(name, "wb"))


