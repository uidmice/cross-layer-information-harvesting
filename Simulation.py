import simpy
import numpy as np
from framework.Node import Node, EnergyProfile
from framework.Gateway import Gateway
from framework.TransmissionInterface import AirInterface
from framework.Backend import Server, Application
from framework.LoRaParameters import LoRaParameters
from framework.Environment import Environment


class Simulation:
    ENVIRONMENT_TYPE = ["temp"]

    def __init__(self, nodes_positions, gateway_positions, info_group, collision_group, step_time, environment: Environment, num_steps, offset=2000):
        self.nodes = []
        self.gateways = []
        assert step_time >= offset + 500
        self.step_time = step_time
        self.offset = offset
        self.steps = 0
        self.num_steps = num_steps
        self.sim_env = simpy.Environment()
        self.channel_group = collision_group
        self.info_group = info_group
        self.channel_nodes = {}
        for channel in range(Gateway.NO_CHANNELS):
            self.channel_nodes[channel] = []

        self.environment = environment
        self.app = Application(len(nodes_positions))
        self.server = Server(self.gateways, self.sim_env, self.app)
        self.air_interface = AirInterface(self.sim_env, self.gateways, self.server)

        for i in range(len(nodes_positions)):
            node = Node(i, EnergyProfile(0.1), LoRaParameters(collision_group[i]),
                                   self.air_interface, self.sim_env, nodes_positions[i], False)
            self.channel_nodes[collision_group[i]].append(i)
            node.last_payload_sent = self.environment.sense(i, 0)
            self.nodes.append(node)
        for i in range(len(gateway_positions)):
            self.gateways.append(Gateway(i, gateway_positions[i], self.sim_env))

        self.constructed_field = []
        self.temp_field = []

        self.status = {'total_transmission': 0, 'successful_transmission' : 0}



    def node_states(self, *args, **kwargs):
        return list(a.get_status(*args, **kwargs) for a in self.nodes)

    def step(self, actions):
        assert len(self.nodes) == len(actions)
        assert self.sim_env.now == self.steps * self.step_time
        self.constructed_field = self.field_reconstruction()
        self.temp_field = self.environment.field(self.sim_env.now)
        self.steps += 1
        send_index = [idx for idx, send in enumerate(actions) if send]
        for i in range(len(self.nodes)):
            self.sim_env.process(self._node_send_sensed_value(i, actions[i]))
        self.sim_env.run(self.step_time * self.steps)
        received = []
        for i in send_index:
            if self.nodes[i].packet_to_send.received:
                received.append(i)
        return send_index, received

    def _node_send_sensed_value(self, node_index, send):
        node = self.nodes[node_index]
        value = node.sense(self.environment)
        time = self.sim_env.now
        yield self.sim_env.timeout(np.random.randint(self.offset))
        if send:
            packet = node.create_unique_packet({'value':value, 'time': time}, False, False)
            packet.airtime(500)
            yield self.sim_env.process(node.send(packet))
        yield self.sim_env.timeout(self.step_time * self.steps - self.sim_env.now)

    def _node_send_test(self, node_index):
        yield self.sim_env.timeout(np.random.randint(self.offset))
        node = self.nodes[node_index]
        packet = node.create_unique_packet(None, True, True)
        yield self.sim_env.process(node.send(packet))
        yield self.sim_env.timeout(self.step_time * self.steps - self.sim_env.now)

    def reset(self, reset_lora=False):
        self.sim_env = simpy.Environment()
        self.steps = 0
        for i in range(len(self.nodes)):
            self.nodes[i].reset(self.sim_env)
            self.nodes[i].last_payload_sent = self.environment.sense(i, 0)
            if reset_lora:
                self.nodes[i].para = LoRaParameters(i % Gateway.NO_CHANNELS, sf=12)
        for i in range(len(self.gateways)):
            self.gateways[i].reset(self.sim_env)
        self.server.reset(self.sim_env)
        self.air_interface.reset(self.sim_env)
        self.status['successful_transmission'] = 0
        self.status['total_transmission'] = 0

    def field_reconstruction(self):
        prediction = self.app.predict()
        return prediction


    def aloha(self, G, seed=4):
        idx = 0
        frametime = 300
        T = frametime *500
        interval = frametime/G
        rnd = np.random.RandomState(seed)
        while self.sim_env.now < T:
            yield self.sim_env.timeout(rnd.exponential(interval))
            packet = self.nodes[idx].create_unique_packet(0, False, False)
            packet.airtime(frametime)
            self.sim_env.process(self.nodes[idx].send(packet, self.status))
            idx += 1
            idx %= len(self.nodes)
