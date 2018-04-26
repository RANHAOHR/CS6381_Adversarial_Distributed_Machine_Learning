import os
import sys
import time
import threading
import zmq
from random import randrange
import pprint

class Scheduler():
    """Implementation of the scheduler for synchronization"""
    def __init__(self):
        self.context = zmq.Context()
        self.results_receiver = self.context.socket(zmq.PULL)
        self.results_receiver.bind("tcp://127.0.0.1:5558")

    def result_collector(self):
        collecter_data = {}
        for x in xrange(1000):
            result = self.results_receiver.recv_json()
            if collecter_data.has_key(result['consumer']):
                collecter_data[result['consumer']] = collecter_data[result['consumer']] + 1
            else:
                collecter_data[result['consumer']] = 1
            if x == 999:
                pprint.pprint(collecter_data)

if __name__ == '__main__':
    scheduler = Scheduler()
    scheduler.result_collector()