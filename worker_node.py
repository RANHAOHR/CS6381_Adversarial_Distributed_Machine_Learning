import time
import zmq
import random
import os
import sys

class Worker:
    """Implementation of the worker for gradient computation"""
    def __init__(self, consumer_id, scheduler_addr):
        self.consumer_id = consumer_id
        print "I am woker #%s" % (self.consumer_id)
        self.context = zmq.Context()
        self.scheduler_addr = "tcp://" + scheduler_addr + ":5557"
        self.worker_addr = "tcp://" + scheduler_addr + ":5558"
        # recieve work
        self.consumer_receiver = self.context.socket(zmq.PULL)
        self.consumer_receiver.connect(self.scheduler_addr)
        # send work
        self.consumer_sender = self.context.socket(zmq.PUSH)
        self.consumer_sender.connect(self.worker_addr)

    def consumer(self):        
        while True:
            work = self.consumer_receiver.recv_json()
            data = work['num']
            print("the received data is: ", data )
            result = { 'consumer' : self.consumer_id, 'num' : data}
            if data%2 == 0: 
                self.consumer_sender.send_json(result)
                print("sending to producer!")

if __name__ == '__main__':
    consumer_id = sys.argv[1] if len(sys.argv) > 1 else "10001"
    scheduler_addr = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
    port = sys.argv[3] if len(sys.argv) > 3 else ""

    worker = Worker(consumer_id, scheduler_addr)
    worker.consumer()