import os
import sys
import time
import threading
import zmq
from random import randrange
import pprint

class Scheduler():
    """Implementation of the scheduler for synchronization"""
    def __init__(self, sever_addr):
        # self.server_addr = 
        self.context = zmq.Context()
        self.results_receiver = self.context.socket(zmq.PULL)
        self.results_receiver.bind("tcp://*:5559")

    def result_collector(self):
        collecter_data = {}
        for x in xrange(1000):
            result = self.results_receiver.recv_json()
            print("result: ", result['worker'])
            if collecter_data.has_key(result['worker']):
                collecter_data[result['worker']] = collecter_data[result['worker']] + 1
            else:
                collecter_data[result['worker']] = 1
            if x == 999:
                pprint.pprint(collecter_data)

if __name__ == '__main__':
    server_addr = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    scheduler = Scheduler(server_addr)
    scheduler.result_collector()