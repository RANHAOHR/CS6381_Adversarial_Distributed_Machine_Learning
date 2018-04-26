# Sample code for CS6381
# Vanderbilt University
# Instructor: Aniruddha Gokhale
#
# Code taken from ZeroMQ examples with additional
# comments or extra statements added to make the code
# more self-explanatory or tweak it for our purposes
#
# We are executing these samples on a Mininet-emulated environment
import os
import sys
import time
import threading
import zmq
from random import randrange
import pprint

class Server:
    """Implementation of the server for weights gathering"""
    def __init__(self):
        self.context = zmq.Context()
        self.results_receiver = self.context.socket(zmq.PULL)
        self.results_receiver.bind("tcp://*:5558")     
        self.zmq_socket = self.context.socket(zmq.PUSH)
        self.zmq_socket.bind("tcp://*:5557")   

        self.threading_obj = threading.Thread(target=self.receiving)
        self.threading_obj.daemon = True
        self.threading_obj.start()

    def receiving(self):
        collecter_data = {}
        for x in xrange(1000):
            result = self.results_receiver.recv_json()
            print("result: ", result['consumer'])
            if collecter_data.has_key(result['consumer']):
                collecter_data[result['consumer']] = collecter_data[result['consumer']] + 1
            else:
                collecter_data[result['consumer']] = 1
            if x == 999:
                pprint.pprint(collecter_data)

    def producer(self):
        # Start your result manager and workers before you start your producers
        for num in xrange(20000):
            work_message = { 'num' : num }
            self.zmq_socket.send_json(work_message)


if __name__ == '__main__':
    server = Server()
    server.producer()
    
 

