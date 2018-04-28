__author__ = 'Ehsan'
from mininet.node import CPULimitedHost
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel, info
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.link import TCLink
"""
Instructions to run the topo:
    1. Go to directory where this fil is.
    2. run: sudo -E python <file name>
       In this case it is: sudo -E python Tree_Generic_Topo.py     
"""
n_workers = 3
server_addr = "127.0.0.1" 

class GenericTree(Topo):
    """Simple topology example."""

    def build( self, depth=1, fanout=2 ):
        # Numbering:  h1..N, s1..M
        self.hostNum = 1
        self.switchNum = 1

    def build( self, depth=1, fanout=2 ):
        # Numbering:  h1..N, s1..M
        self.hostNum = 1
        self.switchNum = 1
        # Build topology
        self.addTree(depth, fanout)

    def addTree( self, depth, fanout ):
        """Add a subtree starting with node n.
           returns: last node added"""
        isSwitch = depth > 0
        if isSwitch:
            node = self.addSwitch( 's%s' % self.switchNum )
            self.switchNum += 1
            for _ in range( fanout ):
                child = self.addTree( depth - 1, fanout)
                self.addLink( node, child )
        else:
            node = self.addHost( 'h%s' % self.hostNum )
            self.hostNum += 1
        return node


def run():
    c = RemoteController('c', '0.0.0.0', 6633)
    # Change the args of GenericTree() to your desired values. You could even get them from command line.
    net = Mininet(topo=GenericTree(depth=1, fanout=6), host=CPULimitedHost, controller=None)
    net.addController(c)
    net.start()

    # installStaticFlows( net )
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

    net.stop()
    
def startWroker(net, i,consumer_id, port, server_addr, scheduler_addr):
    h = net.get('h%i' % i)
    print("h is", h)
    h.cmd('python worker_node.py %s %s %s %s &'\
        % (consumer_id, port, server_addr, scheduler_addr))

def startServer(net, i):
    h = net.get('h%i' % i)
    h.cmd('python server_node.py')
    server_addr  = "10.0.0." + str(i)

# if the script is run directly (sudo custom/optical.py):
if __name__ == '__main__':
    setLogLevel('info')
    run()