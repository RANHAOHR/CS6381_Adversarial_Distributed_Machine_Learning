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
n_batch = 2

epoch = 1000

class Server:
    """Implementation of the server for weights gathering"""
    def __init__(self):
        self.context = zmq.Context()
        batch_port = 5558
        self.results_receivers = []
        self.register = []
        self.counter = []
        self.w_batch = np.zeros([n_machine, n_feat])

        self.w_new = np.zeros(n_feat)
        self.signal = []

        self.zk_object = KazooClient(hosts='127.0.0.1:2181') 
        self.zk_object.start()

        self.workers = []
        port = 5560
        self.scheduler_path = '/scheduler/'
        self.mini_batch = []
        for i in range(n_batch):
            self.scheduler_node = self.scheduler_path + "node_" + str(i) #initialize the batch node name
            self.mini_batch.append(self.scheduler_node)

            self.register.append([0,0,0]) # initialize the counter and reigister for the batches
            self.counter.append(0)
            batch_addr = "tcp://*:"+ str(batch_port) #initialize the receiveing addr from the worker, each batch has an addr
            self.results_receiver = self.context.socket(zmq.PULL)
            self.results_receiver.bind(batch_addr)
            self.results_receivers.append(self.results_receiver)
            batch_port += 1
            self.signal.append(1)

            for x in range(i*n_machine, (i+1)*n_machine):
                worker_zmq = self.context.socket(zmq.PUSH)
                str_port = str(port)
                temp_addr = "tcp://*:" + str_port
                worker_zmq.bind(temp_addr)
                self.workers.append(worker_zmq)
                port += 1
                print("self.workers",temp_addr )


        self.scheduler_thread = threading.Thread(target=self.scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()

    def receiving(self):
        ''' starting the initialization of all worker nodes with 0 weights '''
        work_message = { 'num' : self.w_new.tolist()} #avoid deadlock, send initials
        for x in range(n_batch*n_machine):
            print("Finish initialize of worker node ", x)
            self.workers[x].send_json(work_message)
        time.sleep(1)
        print("finished")

        while self.counter[0] <= epoch or self.counter[1] <= epoch:
            for j in range(n_batch):         
                if self.signal[j] == 1:
                    result = self.results_receivers[j].recv_json()
                    w_value = np.array(result['num'])
                    print("server receives:", w_value)
                    w_id = int(result['worker'])
                    w_id = w_id %3
                    self.w_batch[w_id] = w_value
                    self.register[j][w_id] = 1
                    if sum(self.register[j]) == n_machine:
                        self.w_new = np.mean(self.w_batch, axis=0)
                        self.producer(j)
                else:
                    self.counter[j] = epoch+1
                    print("stop send to worker batch: ", j)
                    pass


    def producer(self, i_batch):
        # Start your result manager and workers before you start your producers
        work_message = { 'num' : self.w_new.tolist()}
        # print("work_message", work_message)
        for x in range(i_batch*n_machine, (i_batch+1)*n_machine):
            self.workers[x].send_json(work_message)
            pass
        self.register[i_batch] = [0,0,0]
        self.counter[i_batch] += 1
        print("self.counter ", self.counter[i_batch] )
        # computer the loss
        error = np.dot(X_train, self.w_new)-y_train
        squared_error = np.dot(error,error)
        rmse = math.sqrt(squared_error/n_train)
        print(self.counter, rmse)

    def scheduler(self):
        while True:
            try:
                @self.zk_object.DataWatch(self.mini_batch[0])
                def watch_scheduler_0(data, stat, event):
                    if event != None: #wait for event to be alive and None(stable)
                        if event.type == "DELETED":
                            self.signal[0] = 0
                            
                    time.sleep(0.5) #easy to stop the code

                @self.zk_object.DataWatch(self.mini_batch[1])
                def watch_scheduler_1(data, stat, event):
                    if event != None: #wait for event to be alive and None(stable)
                        if event.type == "DELETED":
                            self.signal[1] = 0
                            
                    time.sleep(0.5) #easy to stop the code

            except KeyboardInterrupt:
                return -1



if __name__ == '__main__':
    server = Server()
    server.receiving()
