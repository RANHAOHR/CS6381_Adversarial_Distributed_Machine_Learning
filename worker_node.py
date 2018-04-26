import time
import zmq
import random
import os
import sys

class Worker:
    """Implementation of the worker for gradient computation"""
    def __init__(self, consumer_id, server_addr, scheduler_addr):
        self.consumer_id = consumer_id
        print "I am woker #%s" % (self.consumer_id)
        self.context = zmq.Context()
        self.server_addr = "tcp://" + server_addr + ":5557"
        self.worker_addr = "tcp://" + server_addr + ":5558"
        self.scheduler_addr = "tcp://" + scheduler_addr + ":5559"
        # recieve work
        self.consumer_receiver = self.context.socket(zmq.PULL)
        self.consumer_receiver.connect(self.server_addr)
        # send work
        self.server_sender = self.context.socket(zmq.PUSH)
        self.server_sender.connect(self.worker_addr)

        self.scheduler_sender = self.context.socket(zmq.PUSH)
        self.scheduler_sender.connect(self.scheduler_addr)       

    def consumer(self):        
        while True:
            work = self.consumer_receiver.recv_json()
            data = work['num']
            print("the received data is: ", data )
            result = { 'worker' : self.consumer_id, 'num' : data}
            if data%2 == 0: 
                self.server_sender.send_json(result)
                print("sending to producer!")
                self.scheduler_sender.send_json(result)

if __name__ == '__main__':
    consumer_id = sys.argv[1] if len(sys.argv) > 1 else "10001"
    server_addr = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
    scheduler_addr = sys.argv[3] if len(sys.argv) > 3 else "127.0.0.1"

    worker = Worker(consumer_id, server_addr, scheduler_addr)
    worker.consumer()