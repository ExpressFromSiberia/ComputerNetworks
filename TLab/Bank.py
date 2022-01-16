from random import random

import Communication
import Network


class Bank:

    def __init__(self, conn, index, credit_rate):
        self.index = index
        self.credit_rate = credit_rate
        self.CB_connection = conn
        self.neighbors = []
        self.shortest_roads = None
        self.neighbors_connections = None
        self.topology = Network.Topology()

    def cheater_create(self):
        self.credit_rate *= 5

    def send_neighbors(self):
        msg = Communication.Message()
        msg.type = Communication.MsgType.NEIGHBORS
        msg.data = self.neighbors.copy()
        self.CB_connection.send_message(msg)

    def create_bank_network(self):
        for i in range(len(self.neighbors)):
            new_connection = Communication.Connection()
            self.neighbors_connections.append(new_connection)

    def get_topology(self):
        msg = Communication.Message()
        msg.type = Communication.MsgType.GET_TOPOLOGY
        self.CB_connection.send_message(msg)

    def request_rate(self, suspect_id, suspect_conn):
        msg = Communication.Message()
        msg.type = Communication.MsgType.REQUEST_RATE
        msg.data = {"index": suspect_id, "sender": self.index, "sender_connection": self.CB_connection}
        print(f"Bank {self.index} start suspect")
        suspect_conn.send_message(msg, 1)

    def send_rate(self, sender, sender_conn):
        msg = Communication.Message()
        msg.type = Communication.MsgType.RECEIVE_RATE
        msg.data = {"index": sender, "rate": self.credit_rate, "sender": self.index}
        print(f"Bank {self.index} send his rate")
        sender_conn.send_message(msg, 1)

    def receive_rate(self, rate, suspect):
        print(f"Bank {self.index} received suspect rate = {rate}")
        if rate > self.credit_rate + 0.1*random() or rate < self.credit_rate - 0.1*random():
            decision = 1
        else:
            decision = -1

        msg = Communication.Message()
        msg.type = Communication.MsgType.DECISION_SINGLE
        msg.data = {"decision": decision, "sender": self.index, "suspect": suspect}
        self.CB_connection.send_message(msg)

    def bank_connect(self):
        self.send_neighbors()
        self.get_topology()
        print(f"Bank {self.index} is connected with rate {self.credit_rate}.")

    def bank_disconnect(self):
        msg = Communication.Message()
        msg.type = Communication.MsgType.OFF
        self.CB_connection.send_message(msg)
        print(f"Bank {self.index} disconnected.")

    def add_node(self, index, neighbors):
        self.topology.add_new_node(index)
        for j in neighbors:
            self.topology.add_new_link(index, j)

        if index in self.neighbors:
            if index not in self.topology.topology[self.index]:
                msg = Communication.Message()
                msg.type = Communication.MsgType.NEIGHBORS
                msg.data = [index]
                self.CB_connection.send_message(msg)

    def delete_node(self, index):
        self.topology.delete_node(index)

    def proc_message(self):
        input_msg = self.CB_connection.get_message()

        if input_msg is None:
            return

        if input_msg.type == Communication.MsgType.NEIGHBORS:
            index = input_msg.data["index"]
            neighbors = input_msg.data["neighbors"]
            self.add_node(index, neighbors)

        elif input_msg.type == Communication.MsgType.SET_TOPOLOGY:
            new_topology = input_msg.data
            self.topology = new_topology

        elif input_msg.type == Communication.MsgType.OFF:
            index = input_msg.data
            self.delete_node(index)

        elif input_msg.type == Communication.MsgType.RECEIVE_RATE:
            rate = input_msg.data["rate"]
            suspect_id = input_msg.data["sender"]
            self.receive_rate(rate, suspect_id)

        elif input_msg.type == Communication.MsgType.REQUEST_RATE:
            sender = input_msg.data["sender"]
            sender_conn = input_msg.data["sender_connection"]
            self.send_rate(sender, sender_conn)

        elif input_msg.type == Communication.MsgType.ARRANGE_CHECK:
            suspect_id = input_msg.data["suspect_id"]
            suspect_conn = input_msg.data["suspect_connection"]
            self.request_rate(suspect_id, suspect_conn)

        else:
            print(f"Bank {self.index}: unexpected msg type:", input_msg.type, input_msg.data["index"])
