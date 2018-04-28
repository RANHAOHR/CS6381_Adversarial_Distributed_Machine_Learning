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
import numpy as np
import math

from kazoo.client import KazooClient
from kazoo.client import KazooState

import logging

from kazoo.exceptions import (
    ConnectionClosedError,
    NoNodeError,
    KazooException
)

logging.basicConfig() # set up logginga

X_train = 4*np.random.rand(100)
y_train = 2*X_train + 1 + 1*np.random.randn(100)
X_train = np.vstack((X_train,np.ones(np.shape(X_train)))).T
(n_train, n_feat) = X_train.shape
n_machine = 3
epoch = 1000

class Server:
    """Implementation of the server for weights gathering"""
    def __init__(self):
        self.context = zmq.Context()
        self.results_receiver = self.context.socket(zmq.PULL)
        self.results_receiver.bind("tcp://*:5558")

        self.scheduler_receiver = self.context.socket(zmq.PULL)
        self.scheduler_receiver.bind("tcp://*:5559")

        self.workers = []
        port = 5560
        for x in range(n_machine):
            worker_zmq = self.context.socket(zmq.PUSH)
            str_port = str(port)
            temp_addr = "tcp://*:" + str_port
            worker_zmq.bind(temp_addr)
            self.workers.append(worker_zmq)
            port += 1

        self.counter = 0
        self.w_batch = np.zeros([n_machine, n_feat])
        self.register = [0,0,0]
        self.w_new = np.zeros(n_feat)

        self.zk_object = KazooClient(hosts='127.0.0.1:2181') 
        self.zk_object.start()
        self.scheduler_path = '/scheduler/'
        self.scheduler_node = self.scheduler_path + "node_0"

        self.group_1 = 1
        self.scheduler_thread = threading.Thread(target=self.scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()

    def receiving(self):
        ''' starting with the initial 0 weights '''
        work_message = { 'num' : self.w_new.tolist()} #avoid deadlock, send initials
        for x in range(n_machine):
            self.workers[x].send_json(work_message)
            pass

        time.sleep(1)
        while self.counter <= epoch:
            if self.group_1 == 1:
                result = self.results_receiver.recv_json()
                w_value = np.array(result['num'])
                print("server receives:", w_value)
                w_id = int(result['worker'])
                self.w_batch[w_id] = w_value
                self.register[w_id] = 1
                if sum(self.register) == n_machine:
                    self.w_new = np.mean(self.w_batch, axis=0)
                    self.producer()
            else:
                print("stop send to group_1")


    def producer(self):
        # Start your result manager and workers before you start your producers
        work_message = { 'num' : self.w_new.tolist()}
        # print("work_message", work_message)
        for x in range(n_machine):
            self.workers[x].send_json(work_message)
            pass
        self.register = [0,0,0]
        self.counter += 1
        print("self.counter ", self.counter )
        # computer the loss
        error = np.dot(X_train, self.w_new)-y_train
        squared_error = np.dot(error,error)
        rmse = math.sqrt(squared_error/n_train)
        print(self.counter, rmse)
        # else:
            # print("not ready yet!")
    def scheduler(self):
        while True:
            try:
                @self.zk_object.DataWatch(self.scheduler_node)
                def watch_scheduler(data, stat, event):
                    if event != None: #wait for event to be alive and None(stable)
                        if event.type == "CHANGED":
                            self.group_1 = 0
                            # print("scheduler called")
                            
                time.sleep(0.01) #easy to stop the code
            except KeyboardInterrupt:
                return -1



if __name__ == '__main__':
    server = Server()
    server.receiving()
