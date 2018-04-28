from worker_node import Worker
import os
import sys
import time
import zmq
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.clean import cleanup

n_workers = 3
server_addr = "127.0.0.1" 

class SimplePktSwitch(Topo):
    """Simple topology example."""

    def __init__(self, **opts):
        """Create custom topo."""

        # Initialize topology
        # It uses the constructor for the Topo cloass
        super(SimplePktSwitch, self).__init__(**opts)

        # Add hosts and switches
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')
        h5 = self.addHost('h5')
        h6 = self.addHost('h6')

        # Adding switches
        s1 = self.addSwitch('s1', dpid="0000000000000001")

        # Adding switches
        s1 = self.addSwitch('s1', dpid="0000000000000001")
        s2 = self.addSwitch('s2', dpid="0000000000000002")
        s3 = self.addSwitch('s3', dpid="0000000000000003")
        s4 = self.addSwitch('s4', dpid="0000000000000004")
        s5 = self.addSwitch('s5', dpid="0000000000000003")
        s6 = self.addSwitch('s6', dpid="0000000000000004")

        # Add links
        self.addLink(h1, s1)
        self.addLink(h2, s2)
        self.addLink(h3, s3)
        self.addLink(h4, s4)
        self.addLink(h5, s5)
        self.addLink(h6, s6)

        self.addLink(s1, s2)
        self.addLink(s1, s3)
        self.addLink(s1, s4)

def run():
    net = Mininet(topo=SimplePktSwitch(), controller=None)
    net.start()
    CLI(net)
    startServer(net, 1) #run server at host 1
    i = 2
    start_id = 0
    init_port = 5560
    for x in range(0, n_workers):
        consumer_id = str(start_id)
        port = str(init_port)
        startWroker(net, i, consumer_id, server_addr, port, scheduler_addr)

        i +=1
        start_id += 1
        init_port += 1

def startWroker(net, i,consumer_id, port, server_addr, scheduler_addr):
    h = net.get('h%i' % i)
    h.cmd('python worker_node.py %s %s %s %s &'\
        % (consumer_id, port, server_addr, scheduler_addr))

def startServer(net, i):
    h = net.get('h%i' % i)
    h.cmd('python server_node.py')
    server_addr  = "10.0.0." + str(i)

if __name__ == '__main__':
    setLogLevel('info')
    run()