import Bank
import CentralBank
from random import random
from threading import Thread

central_bank = CentralBank.CentralBank()


def bank_connection(neighbors):
    global central_bank

    conn, index = central_bank.add_connection()
    cb_rate, cb_rate_dispersion = central_bank.setting_credit_rate()
    credit_rate = round(cb_rate + cb_rate_dispersion*(2 * random() - 1), 3)
    bank = Bank.Bank(conn, index, credit_rate)
    bank.neighbors = neighbors.copy()
    bank.bank_connect()

    while True:
        bank.proc_message()


def central_bank_connection():
    global central_bank
    central_bank = CentralBank.CentralBank()
    print(f"Central Bank is connected with rate {central_bank.credit_rate}"
          f" and rate {central_bank.credit_rate_dispersion}.")

    while True:
        central_bank.proc_message()


def main():
    money_network = {
        "banks": [0, 1, 2, 3],
        "network": [[1, 2, 3], [0, 2, 3], [0, 1, 3], [0, 1, 2]]
    }
    ln = len(money_network["banks"])

    dr_thread = Thread(target=central_bank_connection, args=())
    node_threads = [Thread(target=bank_connection, args=(money_network["network"][i],)) for i in range(ln)]
    dr_thread.start()
    for i in range(len(money_network["banks"])):
        node_threads[i].start()

    central_bank.arrange_check(2)

    for i in range(ln):
        node_threads[i].join()
    dr_thread.join()


if __name__ == '__main__':
    main()
