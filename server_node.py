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
from threading import Lock
import zmq
from random import randrange
import numpy as np
import math
import matplotlib.pyplot as plt


from kazoo.client import KazooClient
from kazoo.client import KazooState

import logging
import pandas as pd
from sklearn.cross_validation import train_test_split
from sklearn.preprocessing import StandardScaler


from kazoo.exceptions import (
    ConnectionClosedError,
    NoNodeError,
    KazooException
)

logging.basicConfig() # set up logginga

def load_data(path):
    data = pd.read_csv(path, header=None)
    X = data.iloc[:, :-1].values
    y = data.iloc[:, -1].values
    return (X, y)

mutex = Lock()
#X_train = 4*np.random.rand(100)
#y_train = 2*X_train + 1 + 1*np.random.randn(100)
#X_train = np.vstack((X_train,np.ones(np.shape(X_train)))).T

(X,y) = load_data("boston_housing.csv")
scaler = StandardScaler()
X = scaler.fit_transform(X)
data = np.concatenate([X, np.ones((X.shape[0], 1)), y.reshape((len(y), 1))], axis=1)
#train_data, test_data = train_test_split(data, train_size=0.5)
train_data = data
X_train, y_train = train_data[:, :-1], train_data[:, -1]


(n_train, n_feat) = X_train.shape
n_machine = 3
n_batch = 2

epoch = 1000

def evade_lr(x_start, z, cost_param, w):
    w_n = w[0:-1]
    w_b = w[-1]
    x_start = x_start[0:-1]
    x = np.copy(x_start)
    z_prime = z-w_b
    show_loss = []
    for evade_step in range(1000):
        x = x-0.0001*2*((np.dot(w_n, x)-z_prime)*w_n+cost_param*(x-x_start))
        loss = (np.dot(w_n, x)+w_b-z)**2 + cost_param*np.dot(x-x_start, x-x_start)
        show_loss.append(loss)
    x = np.append(x, 1)
    #plt.plot(range(1000),show_loss)
    #plt.show()
    return x

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
        self.RMSE = []

        self.signal = []
        self.live_batch = 0

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

        self.multibatch_thread = threading.Thread(target=self.multi_batch)
        self.multibatch_thread.daemon = True
        self.multibatch_thread.start()

    def receiving(self):
        fig = plt.figure()
        ax = fig.add_subplot(1,1,1)
        plt.ion()
        plt.show()
        ''' starting the initialization of all worker nodes with 0 weights '''
        work_message = { 'num' : self.w_new.tolist()} #avoid deadlock, send initials
        for x in range(n_batch*n_machine):
            print("Finish initialize of worker node ", x)
            self.workers[x].send_json(work_message)
        time.sleep(1)
        print("finished")

        while self.counter[0] <= epoch or self.counter[1] <= epoch:
            self.process(0)
            mutex.acquire()
            lines = ax.plot(range(len(self.RMSE)), self.RMSE, 'r-', lw=2)
            mutex.release()
            plt.xlabel('Epoch')
            plt.ylabel('RMSE')
            plt.xticks([0, 200, 400, 600, 800, 1000], ['0', '200', '400', '600', '800', '1000'])
            plt.yticks([0, 5, 10, 15, 20, 25, 30],['0', '5', '10', '15', '20', '25', '30'])
            plt.pause(0.01)

        # plt.savefig("results", bbox_inches="tight")
        # plt.close() 
        ''' start to evade'''
        x_start = X_train[36]
        x_adv = evade_lr(x_start, 33, 30, self.w_new)
        y_adv = np.dot(self.w_new, x_adv)
        # make data feasible
        x_adv[0] = x_start[0]
        x_adv[1] = x_start[1]

        y_pred = np.dot(self.w_new, x_start)
        y_adv = np.dot(self.w_new, x_adv)
        x_start_raw = scaler.inverse_transform(np.array([x_start[0:-1]]))
        x_adv_raw = scaler.inverse_transform(np.array([x_adv[0:-1]]))

        np.set_printoptions(precision=2, suppress=True)
        print("Original data", x_start_raw[0])
        print("Predicted price before attack:",y_pred)
        
        print("Adversarial data", x_adv_raw[0])
        print("Predicted price after attack",y_adv)

    def process(self, j):
        if self.signal[j] == 1:
            result = self.results_receivers[j].recv_json()
            w_value = np.array(result['num'])
            # print("server receives:", w_value)
            w_id = int(result['worker'])
            w_id = w_id %3
            self.w_batch[w_id] = w_value
            self.register[j][w_id] = 1
            mutex.acquire()
            if sum(self.register[j]) == n_machine:
                self.w_new = np.mean(self.w_batch, axis=0)
                # compute loss and then plot
                error = np.dot(X_train, self.w_new)-y_train
                squared_error = np.dot(error,error)
                rmse = math.sqrt(squared_error/n_train)
                if self.live_batch == j:
                    self.RMSE.append(rmse)
                    pass
                print(self.counter, rmse)
                self.producer(j)
            mutex.release()
        else:
            self.counter[j] = epoch+1
            print("stop send to worker batch: ", j)
            pass

    def multi_batch(self):
        while self.counter[1] <= epoch: 
            self.process(1) 
            if self.signal[0] == 1:
                time.sleep(0.5) #compensation for drawing time in main thread
            else:
                time.sleep(0.01) #compensation for drawing time in main thread

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

    def scheduler(self):
        while True:
            try:
                @self.zk_object.DataWatch(self.mini_batch[0])
                def watch_scheduler_0(data, stat, event):

                    if event != None: #wait for event to be alive and None(stable)
                        if event.type == "DELETED":
                            # print("deleted")
                            self.live_batch = 1
                            self.signal[0] = 0
                            
                    time.sleep(0.1) #easy to stop the code

                @self.zk_object.DataWatch(self.mini_batch[1])
                def watch_scheduler_1(data, stat, event):
                    if event != None: #wait for event to be alive and None(stable)
                        if event.type == "DELETED":
                            self.live_batch = 0
                            self.signal[1] = 0
                            
                    time.sleep(0.1) #easy to stop the code

            except KeyboardInterrupt:
                return -1



if __name__ == '__main__':
    server = Server()
    server.receiving()
