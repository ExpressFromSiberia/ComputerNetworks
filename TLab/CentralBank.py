import Communication
import Network


class CentralBank:

    def __init__(self):
        self.credit_rate = 4
        self.credit_rate_dispersion = 0.2
        self.decision_res = 0
        self.num_decisions = 0
        self.connections = []
        self.new_suspects = []
        self.topology = Network.Topology()

    def change_credit_rate(self, new_rate):
        self.credit_rate = new_rate

    def change_credit_rate_dispersion(self, new_dispersion):
        self.credit_rate_dispersion = new_dispersion

    def setting_credit_rate(self):
        return self.credit_rate, self.credit_rate_dispersion

    def arrange_check(self, suspect_id):
        msg = Communication.Message()
        msg.type = Communication.MsgType.ARRANGE_CHECK
        msg.data = {"suspect_id": suspect_id, "suspect_connection": self.connections[suspect_id]}
        self.send_all_exclude_one(suspect_id, msg)

    def decision(self, suspect, decision, sender):
        print(f"Bank {sender} sent his decision is {decision} about suspect Bank {suspect}")
        self.decision_res += decision
        self.num_decisions += 1
        if decision == -1:
            self.new_suspects.append(sender)
        if self.num_decisions == len(self.connections) - 1:
            print(f"Central Bank is started reviewing decisions about {suspect}")
            if decision > 0:
                self.delete_node(suspect)
                print(f"Suspect {suspect} was a scammer, new list of suspects - {self.new_suspects}")
            else:
                print(f"Suspect {suspect} wasn't a scammer")

    def add_connection(self):
        new_connection = Communication.Connection()
        new_index = len(self.connections)
        self.connections.append(new_connection)
        return new_connection, new_index

    def add_node(self, index, neighbors):
        self.topology.add_new_node(index)
        for j in neighbors:
            self.topology.add_new_link(index, j)

    def delete_node(self, index):
        self.topology.delete_node(index)

    def send_all_exclude_one(self, exclude_index, msg):
        for conn_ind in range(len(self.connections)):
            conn = self.connections[conn_ind]
            if conn is None:
                continue
            if conn_ind == exclude_index:
                continue
            msg.data.update({"index": conn_ind})
            conn.send_message(msg, 1)

    def proc_msg_neighbors(self, conn_ind, input_msg):
        self.add_node(conn_ind, input_msg.data)

        msg = Communication.Message()
        msg.type = Communication.MsgType.NEIGHBORS
        msg.data = {"index": conn_ind, "neighbors": input_msg.data}
        self.send_all_exclude_one(conn_ind, msg)

    def proc_msg_off(self, conn_ind):
        self.delete_node(conn_ind)

        msg = Communication.Message()
        msg.type = Communication.MsgType.OFF
        msg.data = conn_ind

        self.send_all_exclude_one(conn_ind, msg)

    def print_shortest_ways(self):
        msg = Communication.Message()
        msg.type = Communication.MsgType.PRINT_WAYS
        for conn in self.connections:
            conn.send_message(msg, 1)

    def proc_message(self):
        for conn_ind in range(len(self.connections)):
            conn = self.connections[conn_ind]
            if conn is None:
                continue

            input_msg = conn.get_message(1)

            if input_msg is None:
                continue

            if input_msg.type == Communication.MsgType.NEIGHBORS:
                self.proc_msg_neighbors(conn_ind, input_msg)

            elif input_msg.type == Communication.MsgType.GET_TOPOLOGY:
                msg = Communication.Message()
                msg.type = Communication.MsgType.SET_TOPOLOGY
                msg.data = self.topology.copy()
                conn.send_message(msg, 1)

            elif input_msg.type == Communication.MsgType.DECISION_SINGLE:
                suspect = input_msg.data["suspect"]
                decision = input_msg.data["decision"]
                sender = input_msg.data["sender"]
                self.decision(suspect, decision, sender)

            elif input_msg.type == Communication.MsgType.OFF:
                self.proc_msg_off(conn_ind)

            else:
                print("Central Bank: unexpected msg type:", input_msg.type)
