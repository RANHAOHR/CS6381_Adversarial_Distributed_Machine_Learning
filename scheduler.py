import os
import sys
import time
import zmq
from random import randrange
from kazoo.client import KazooClient
from kazoo.client import KazooState

import logging

from kazoo.exceptions import (
    ConnectionClosedError,
    NoNodeError,
    KazooException
)

logging.basicConfig() # set up logginga

n_machine = 3
class Scheduler():
    """Implementation of the scheduler for synchronization"""
    def __init__(self,scheduler_id, sever_addr):
        self.context = zmq.Context()

        self.scheduler_id = scheduler_id
        self.zk_object = KazooClient(hosts='127.0.0.1:2181') 
        self.zk_object.start()
        self.path = '/worker/'
        self.worker_nodes = []

        self.batch_index = int(scheduler_id)
        for x in range(self.batch_index*n_machine, (self.batch_index+1)*n_machine):
            node_name = "node_" + str(x)
            worker_node = self.path + node_name 
            self.worker_nodes.append(worker_node)  
        print("self.worker_nodes", self.worker_nodes)   

        self.scheduler_path = '/scheduler/'
        node_name = "node_" + self.scheduler_id
        self.scheduler_node = self.scheduler_path + node_name
        if self.zk_object.exists(self.scheduler_node):
            pass
        else:
            # Ensure a path, create if necessary
            self.zk_object.ensure_path(self.scheduler_path)
            # Create a node with data
            self.zk_object.create(self.scheduler_node) 
            self.zk_object.set(self.scheduler_node, b"0")
        print("self.scheduler_node", self.scheduler_node)

    def worker_watcher(self): #default 3 workers
        batch_num = self.batch_index*n_machine
        while True:
            try:         
                if self.zk_object.exists(self.worker_nodes[0]):
                    @self.zk_object.DataWatch(self.worker_nodes[0])
                    def watch_node_0(data, stat, event):
                        if event != None: #wait for event to be alive and None(stable)
                            if event.type == "DELETED":
                                print("node %s is deleted"%batch_num)
                                if self.zk_object.exists(self.scheduler_node):
                                    self.zk_object.delete(self.scheduler_node)
                            elif event.type == "CREATED":
                                print("worker node 0 is working fine")
                                pass
                        time.sleep(0.5) #easy to stop the code
            except KeyboardInterrupt:
                return -1
            try:            
                if self.zk_object.exists(self.worker_nodes[1]):
                    @self.zk_object.DataWatch(self.worker_nodes[1])
                    def watch_node_1(data, stat, event):
                        if event != None: #wait for event to be alive and None(stable)
                            if event.type == "DELETED":
                                print("node %s is deleted"%(batch_num+1))
                                if self.zk_object.exists(self.scheduler_node):
                                    self.zk_object.delete(self.scheduler_node)
                                    return -1

                            elif event.type == "CREATED":
                                print("worker node 1 is working fine")
                                pass
                        time.sleep(0.5) #easy to stop the code
            except KeyboardInterrupt:
                return -1

            try:             
                if self.zk_object.exists(self.worker_nodes[2]):
                    @self.zk_object.DataWatch(self.worker_nodes[2])
                    def watch_node_2(data, stat, event):
                        if event != None: #wait for event to be alive and None(stable)
                            if event.type == "DELETED":
                                print("node %s is deleted"%(batch_num+2))
                                if self.zk_object.exists(self.scheduler_node):
                                    self.zk_object.delete(self.scheduler_node)
                                pass
                            elif event.type == "CREATED":
                                print("worker node 2 is working fine")
                                pass
                        time.sleep(0.5) #easy to stop the code
            except KeyboardInterrupt:
                return -1


if __name__ == '__main__':
    scheduler_id = sys.argv[1] if len(sys.argv) > 1 else "0"
    server_addr = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
    scheduler = Scheduler(scheduler_id, server_addr)
    scheduler.worker_watcher()