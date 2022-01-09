import matplotlib.pyplot as plt
from threading import Thread
from FLab_Tools import MsgQueue, Message, MessageStatus, time, np, enum

send_msg_queue = MsgQueue()
answer_msg_queue = MsgQueue()

posted_msgs = []
received_msgs = []


def GoBackNSource(window_size, max_number, timeout):
    curr_number = 0
    last_ans_number = -1
    start_time = time.time()
    while last_ans_number < max_number:
        expected_number = (last_ans_number + 1) % window_size

        if answer_msg_queue.has_msg():
            ans = answer_msg_queue.get_message()
            if ans.number == expected_number:
                last_ans_number += 1
                start_time = time.time()
            else:
                curr_number = last_ans_number + 1

        if time.time() - start_time > timeout:
            curr_number = last_ans_number + 1
            start_time = time.time()

        if (curr_number < last_ans_number + window_size) and (curr_number <= max_number):
            k = curr_number % window_size
            msg = Message()
            msg.number = k
            msg.real_number = curr_number
            send_msg_queue.send_message(msg)
            posted_msgs.append(f"{curr_number}({k})")

            curr_number += 1
        pass

    msg = Message()
    msg.data = "STOP"
    send_msg_queue.send_message(msg)


def GoBackNReceiver(window_size):
    expected_number = 0
    while True:
        if send_msg_queue.has_msg():
            curr_msg = send_msg_queue.get_message()
            if curr_msg.data == "STOP":
                break

            if curr_msg.status == MessageStatus.LOST:
                continue

            if curr_msg.number == expected_number:
                ans = Message()
                ans.number = curr_msg.number
                answer_msg_queue.send_message(ans)

                received_msgs.append(f"{curr_msg.real_number}({curr_msg.number})")
                expected_number = (expected_number + 1) % window_size

            else:
                continue


def SelectiveRepeatSource(window_size, max_number, timeout):
    class WndMsgStatus(enum.Enum):
        BUSY = enum.auto()
        NEED_REPEAT = enum.auto()
        CAN_BE_USED = enum.auto()

    class WndNode:
        def __init__(self, number):
            self.status = WndMsgStatus.NEED_REPEAT
            self.time = 0
            self.number = number
            pass

        def __str__(self):
            return f"( {self.number}, {self.status}, {self.time})"

    wnd_nodes = [WndNode(i) for i in range(window_size)]
    ans_count = 0

    while ans_count < max_number:

        res_str = "["
        for i in range(window_size):
            res_str += wnd_nodes[i].__str__()
        res_str += "]"

        if answer_msg_queue.has_msg():
            ans = answer_msg_queue.get_message()
            ans_count += 1
            wnd_nodes[ans.number].status = WndMsgStatus.CAN_BE_USED

        curr_time = time.time()
        for i in range(window_size):
            if wnd_nodes[i].number > max_number:
                continue

            send_time = wnd_nodes[i].time
            if curr_time - send_time > timeout:
                wnd_nodes[i].status = WndMsgStatus.NEED_REPEAT

        for i in range(window_size):
            if wnd_nodes[i].number > max_number:
                continue

            if wnd_nodes[i].status == WndMsgStatus.BUSY:
                continue

            elif wnd_nodes[i].status == WndMsgStatus.NEED_REPEAT:

                wnd_nodes[i].status = WndMsgStatus.BUSY
                wnd_nodes[i].time = time.time()

                msg = Message()
                msg.number = i
                msg.real_number = wnd_nodes[i].number
                send_msg_queue.send_message(msg)
                posted_msgs.append(f"{msg.real_number}({msg.number})")

            elif wnd_nodes[i].status == WndMsgStatus.CAN_BE_USED:
                wnd_nodes[i].status = WndMsgStatus.BUSY
                wnd_nodes[i].time = time.time()
                wnd_nodes[i].number = wnd_nodes[i].number + window_size

                if wnd_nodes[i].number > max_number:
                    continue

                msg = Message()
                msg.number = i
                msg.real_number = wnd_nodes[i].number
                send_msg_queue.send_message(msg)
                posted_msgs.append(f"{msg.real_number}({msg.number})")

    msg = Message()
    msg.data = "STOP"
    send_msg_queue.send_message(msg)


def SelectiveRepeatReceiver(window_size):

    while True:
        if send_msg_queue.has_msg():
            curr_msg = send_msg_queue.get_message()

            if curr_msg.data == "STOP":
                break

            if curr_msg.status == MessageStatus.LOST:
                continue

            ans = Message()
            ans.number = curr_msg.number
            answer_msg_queue.send_message(ans)
            received_msgs.append(f"{curr_msg.real_number}({curr_msg.number})")


def losing_test():
    global send_msg_queue
    global answer_msg_queue
    global posted_msgs
    global received_msgs

    window_size = 4
    timeout = 0.2
    max_number = 80
    loss_probability_arr = np.linspace(0, 0.9, 9)
    protocol_arr = ["GBN", "SRP"]

    print("p    | GBN             |SRP")
    print("     | t     |k        |t    |  k")

    gbn_k = []
    srp_k = []
    for p in loss_probability_arr:
        table_row = f"{p:.1f}\t"
        send_msg_queue = MsgQueue(p)
        answer_msg_queue = MsgQueue(p)
        posted_msgs = []
        received_msgs = []

        for protocol in protocol_arr:
            if protocol == "GBN":
                sender_th = Thread(target=GoBackNSource, args=(window_size, max_number, timeout))
                receiver_th = Thread(target=GoBackNReceiver, args=(window_size,))
            elif protocol == "SRP":
                sender_th = Thread(target=SelectiveRepeatSource, args=(window_size, max_number, timeout))
                receiver_th = Thread(target=SelectiveRepeatReceiver, args=(window_size,))

            sender_th.start()
            receiver_th.start()

            sender_th.join()
            receiver_th.join()

            k = len(received_msgs) / len(posted_msgs)

            if protocol == "GBN":
                gbn_k.append(k)
            else:
                srp_k.append(k)

        print(table_row)

    fig, ax = plt.subplots()
    ax.plot(loss_probability_arr, gbn_k, label="Go-Back-N")
    ax.plot(loss_probability_arr, srp_k, label="SelectiveRepeat")
    ax.set_xlabel('Вероятность потери p')
    ax.set_ylabel('Коэф. эффективности')
    ax.legend()
    fig.show()

    print("p")
    print(loss_probability_arr)
    print("Go-Back-N")
    print("k")
    print(gbn_k)

    print("SelectiveRepeat")
    print("k")
    print(srp_k)


def window_test():
    global send_msg_queue
    global answer_msg_queue
    global posted_msgs
    global received_msgs

    window_size_arr = range(2, 11)
    timeout = 0.2
    max_number = 80
    loss_probability_arr = 0.4
    send_msg_queue = MsgQueue(loss_probability_arr)
    answer_msg_queue = MsgQueue(loss_probability_arr)
    protocol_arr = ["GBN", "SRP"]

    print("w    | GBN             |SRP")
    print("     | t     |k        |t    |  k")

    gbn_k = []
    srp_k = []
    for window_size in window_size_arr:
        table_row = f"{window_size:}\t"

        posted_msgs = []
        received_msgs = []

        for protocol in protocol_arr:
            if protocol == "GBN":
                sender_th = Thread(target=GoBackNSource, args=(window_size, max_number, timeout))
                receiver_th = Thread(target=GoBackNReceiver, args=(window_size,))
            elif protocol == "SRP":
                sender_th = Thread(target=SelectiveRepeatSource, args=(window_size, max_number, timeout))
                receiver_th = Thread(target=SelectiveRepeatReceiver, args=(window_size,))

            sender_th.start()
            receiver_th.start()

            sender_th.join()
            receiver_th.join()

            k = len(received_msgs) / len(posted_msgs)

            if protocol == "GBN":
                gbn_k.append(k)
            else:
                srp_k.append(k)

        print(table_row)

    fig, ax = plt.subplots()
    ax.plot(window_size_arr, gbn_k, label="Go-Back-N")
    ax.plot(window_size_arr, srp_k, label="SelectiveRepeat")
    ax.set_xlabel('Размер окна N')
    ax.set_ylabel('Коэф. эффективности')
    ax.legend()
    fig.show()

    print("w")
    print(window_size_arr)
    print("Go-Back-N")
    print("k")
    print(gbn_k)

    print("SelectiveRepeat")
    print("k")
    print(srp_k)


def main():
    global send_msg_queue
    global answer_msg_queue

    window_size = 2
    max_number = 100
    timeout = 0.5
    loss_probability = 0.3
    protocol = "GBN"
    send_msg_queue = MsgQueue(loss_probability)
    answer_msg_queue = MsgQueue(loss_probability)

    for p in np.linspace(0, 1, 10):
        window_size = 3

    if protocol == "GBN":
        sender_th = Thread(target=GoBackNSource, args=(window_size, max_number, timeout))
        receiver_th = Thread(target=GoBackNReceiver, args=(window_size,))

    elif protocol == "SRP":
        sender_th = Thread(target=SelectiveRepeatSource, args=(window_size, max_number, timeout))
        receiver_th = Thread(target=SelectiveRepeatReceiver, args=(window_size,))

    else:
        print("unknown protocol: ", protocol)
        return

    sender_th.start()
    receiver_th.start()

    sender_th.join()
    receiver_th.join()

    print(f"posted ({len(posted_msgs)}): \t", posted_msgs)
    print(f"received ({len(received_msgs)}):\t", received_msgs)


if __name__ == '__main__':
    print("------------------------------------------")
    print("losing")
    print("------------------------------------------")
    losing_test()

    print("------------------------------------------")
    print("window")
    print("------------------------------------------")
    window_test()
