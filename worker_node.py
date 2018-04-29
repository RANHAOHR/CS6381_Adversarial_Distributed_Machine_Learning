import time
import zmq
import random
import os
import sys
import numpy as np
import math
import numpy as np

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
learning_rate = 0.005

class Worker:
    """Implementation of the worker for gradient computation"""
    def __init__(self, consumer_id, server_addr, port, scheduler_id):
        self.consumer_id = consumer_id
        print("I am woker #%s" % (self.consumer_id))
        self.context = zmq.Context()

        self.server_addr = "tcp://" + server_addr + ":" + port

        self.batch_port = str(5558 + int(scheduler_id))
        self.worker_addr = "tcp://" + server_addr + ":" + self.batch_port
        # self.scheduler_addr = "tcp://" + scheduler_addr + ":5559"
        # self.scheduler_sender = self.context.socket(zmq.PUSH)
        # self.scheduler_sender.connect(self.scheduler_addr)
        # recieve work
        self.consumer_receiver = self.context.socket(zmq.PULL)
        self.consumer_receiver.connect(self.server_addr)
        # send work
        self.server_sender = self.context.socket(zmq.PUSH)
        self.server_sender.connect(self.worker_addr)
        print("send to : ", self.worker_addr)


        self.w = np.zeros(X_train.shape[1])
        self.counter = 0

        #starting zookeeper objects
        self.zk_object = KazooClient(hosts='127.0.0.1:2181') 
        self.zk_object.start()
        self.path = '/worker/'

        node_name = "node_" + self.consumer_id
        self.worker_node = self.path + node_name
        if self.zk_object.exists(self.worker_node):
            pass
        else:
            # Ensure a path, create if necessary
            self.zk_object.ensure_path(self.path)
            # Create a node with data
            self.zk_object.create(self.worker_node) 
        print("self.worker_node", self.worker_node)

    def consumer(self):
        while True:
            try:
                work = self.consumer_receiver.recv_json()
                self.w = np.array(work['num'])
                print("the received data is: ", self.w )
                i = np.random.randint(0, n_train)
                x_i = X_train[i]
                y_i = y_train[i]
                gradient = (np.dot(self.w, x_i)-y_i)*x_i
                self.w = self.w - learning_rate*gradient
                result = { 'worker' : self.consumer_id, 'num' : self.w.tolist()}
                print("worker sends to server:", result['num'])
                self.server_sender.send_json(result)
                self.counter += 1
                print("counter, ", self.counter)                
            except KeyboardInterrupt:
                print("stopped!")
                self.zk_object.delete(self.worker_node)
                return -1

if __name__ == '__main__':
    consumer_id = sys.argv[1] if len(sys.argv) > 1 else "10001"
    port = sys.argv[2] if len(sys.argv) > 2 else "5560"
    scheduler_id = sys.argv[3] if len(sys.argv) > 3 else "0"
    server_addr = sys.argv[4] if len(sys.argv) > 4 else "127.0.0.1" 

    worker = Worker(consumer_id, server_addr, port, scheduler_id)
    worker.consumer()
