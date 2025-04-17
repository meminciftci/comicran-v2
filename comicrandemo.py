#!/usr/bin/python3

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSSwitch, DefaultController
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
import time

class ComicranTopo(Topo):
    def build(self):
        # RRH switch
        rrh = self.addSwitch('s1')

        # Add vBBU hosts
        vbbu1 = self.addHost('vbbu1', ip='10.0.0.10')
        vbbu2 = self.addHost('vbbu2', ip='10.0.0.20')

        # Add UE hosts
        ue1 = self.addHost('ue1', ip='10.0.0.1')
        ue2 = self.addHost('ue2', ip='10.0.0.2')

        # Connect all hosts to RRH (s1)
        self.addLink(rrh, vbbu1)
        self.addLink(rrh, vbbu2)
        self.addLink(rrh, ue1)
        self.addLink(rrh, ue2)

def simulate_handover(net):
    s1 = net.get('s1')
    vbbu1 = net.get('vbbu1')
    vbbu2 = net.get('vbbu2')
    ue1 = net.get('ue1')

    # Get port numbers using intf names
    vbbu1_port = s1.ports[s1.connectionsTo(vbbu1)[0][0]]
    vbbu2_port = s1.ports[s1.connectionsTo(vbbu2)[0][0]]
    ue1_port   = s1.ports[s1.connectionsTo(ue1)[0][0]]

    print("\n[INFO] Adding OpenFlow rules: ue1 <-> vbbu1")
    s1.dpctl('add-flow', 'arp,actions=flood')
    s1.dpctl('add-flow', f'ip,nw_src=10.0.0.1,nw_dst=10.0.0.10,actions=output:{vbbu1_port}')
    s1.dpctl('add-flow', f'ip,nw_src=10.0.0.10,nw_dst=10.0.0.1,actions=output:{ue1_port}')

    print("\n[INFO] Initial connectivity test: ue1 -> vbbu1")
    net.ping([ue1, vbbu1])

    print("\n[INFO] Simulating handover: ue1 -> vbbu2")
    time.sleep(2)

    s1.dpctl('mod-flows', f'ip,nw_src=10.0.0.1,nw_dst=10.0.0.10,actions=output:{vbbu2_port}')
    s1.dpctl('mod-flows', f'ip,nw_src=10.0.0.10,nw_dst=10.0.0.1,actions=output:{ue1_port}')

    print("\n[INFO] Post-handover connectivity test: ue1 -> vbbu2")
    net.ping([ue1, vbbu2])

def run():
    topo = ComicranTopo()
    net = Mininet(topo=topo, controller=DefaultController, switch=OVSSwitch, link=TCLink, autoSetMacs=True)
    net.start()

    print("\n[INFO] COMIC-RAN demo started. Hosts: ue1, ue2, vbbu1, vbbu2")
    simulate_handover(net)
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()

