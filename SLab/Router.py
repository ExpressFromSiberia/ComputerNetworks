import Communication
import Topology


class Router:

    def __init__(self, conn, index):
        self.DR_connection = conn
        self.topology = Topology.Topology()
        self.shortest_roads = None
        self.index = index
        self.neighbors = []

    def print_shortest_ways(self):
        shortest_ways = self.topology.get_shortest_ways(self.index)
        print(f"Path from {self.index} to other is {shortest_ways}\n", end="")

    def send_neighbors(self):
        msg = Communication.Message()
        msg.type = Communication.MsgType.NEIGHBORS
        msg.data = self.neighbors.copy()
        self.DR_connection.send_message(msg)

    def get_topology(self):
        msg = Communication.Message()
        msg.type = Communication.MsgType.GET_TOPOLOGY
        self.DR_connection.send_message(msg)

    def router_start(self):
        self.send_neighbors()
        self.get_topology()
        print(f"Router_{self.index} is started work.")

    def router_off(self):
        msg = Communication.Message()
        msg.type = Communication.MsgType.OFF
        self.DR_connection.send_message(msg)
        print(f"Router_{self.index} is lost.")

    def add_node(self, index, neighbors):
        self.topology.add_new_node(index)
        for j in neighbors:
            self.topology.add_new_link(index, j)

        if index in self.neighbors:
            if index not in self.topology.topology[self.index]:
                msg = Communication.Message()
                msg.type = Communication.MsgType.NEIGHBORS
                msg.data = [index]
                self.DR_connection.send_message(msg)

    def delete_node(self, index):
        self.topology.delete_node(index)

    def proc_message(self):
        input_msg = self.DR_connection.get_message()

        if input_msg is None:
            return

        # print(f"r({self.index}) : {input_msg}\n", end="")

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

        elif input_msg.type == Communication.MsgType.PRINT_WAYS:
            self.print_shortest_ways()

        else:
            print("DR: unexpected msg type:", input_msg.type)
