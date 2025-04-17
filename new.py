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
        # Core SDN switch
        s1 = self.addSwitch('s1')

        # Add RRH as a host
        rrh = self.addHost('rrh', ip='10.0.0.100')

        # Add vBBU hosts
        vbbu1 = self.addHost('vbbu1', ip='10.0.0.10')
        vbbu2 = self.addHost('vbbu2', ip='10.0.0.20')

        # Add UE hosts
        ue1 = self.addHost('ue1', ip='10.0.0.1')
        ue2 = self.addHost('ue2', ip='10.0.0.2')

        # Connect everything to the SDN switch
        self.addLink(s1, rrh)
        self.addLink(s1, ue1)
        self.addLink(s1, ue2)
        self.addLink(s1, vbbu1)
        self.addLink(s1, vbbu2)

def simulate_handover(net):
    s1 = net.get('s1')
    rrh = net.get('rrh')
    vbbu1 = net.get('vbbu1')
    vbbu2 = net.get('vbbu2')
    ue1 = net.get('ue1')
    ue2 = net.get('ue2')

    # Get port numbers
    ue1_port = s1.ports[s1.connectionsTo(ue1)[0][0]]
    ue2_port = s1.ports[s1.connectionsTo(ue2)[0][0]]
    rrh_port = s1.ports[s1.connectionsTo(rrh)[0][0]]
    vbbu1_port = s1.ports[s1.connectionsTo(vbbu1)[0][0]]
    vbbu2_port = s1.ports[s1.connectionsTo(vbbu2)[0][0]]

    print("\n[INFO] Installing OpenFlow rules: ue1/ue2 -> rrh -> vbbu1")

    # ARP
    s1.dpctl('add-flow', 'arp,actions=flood')

    # Route UE1 & UE2 → RRH
    s1.dpctl('add-flow', f'ip,nw_src=10.0.0.1,nw_dst=10.0.0.100,actions=output:{rrh_port}')
    s1.dpctl('add-flow', f'ip,nw_src=10.0.0.2,nw_dst=10.0.0.100,actions=output:{rrh_port}')
    s1.dpctl('add-flow', f'ip,nw_src=10.0.0.100,nw_dst=10.0.0.1,actions=output:{ue1_port}')
    s1.dpctl('add-flow', f'ip,nw_src=10.0.0.100,nw_dst=10.0.0.2,actions=output:{ue2_port}')

    # RRH forwards to vbbu1 (default state)
    s1.dpctl('add-flow', f'ip,nw_src=10.0.0.100,nw_dst=10.0.0.10,actions=output:{vbbu1_port}')
    s1.dpctl('add-flow', f'ip,nw_src=10.0.0.10,nw_dst=10.0.0.100,actions=output:{rrh_port}')

    print("\n[INFO] Initial connectivity test: ue1 and ue2 -> vbbu1 via rrh")
    net.ping([ue1, vbbu1])
    net.ping([ue2, vbbu1])

    print("\n[INFO] Handover: redirect ue1 -> vbbu2")
    time.sleep(2)
    s1.dpctl('mod-flows', f'ip,nw_src=10.0.0.100,nw_dst=10.0.0.10,nw_src=10.0.0.1,actions=output:{vbbu2_port}')
    s1.dpctl('mod-flows', f'ip,nw_src=10.0.0.10,nw_dst=10.0.0.100,nw_dst=10.0.0.1,actions=output:{rrh_port}')
    net.ping([ue1, vbbu2])

    print("\n[INFO] Handover: redirect ue2 -> vbbu2")
    time.sleep(2)
    s1.dpctl('mod-flows', f'ip,nw_src=10.0.0.100,nw_dst=10.0.0.10,nw_src=10.0.0.2,actions=output:{vbbu2_port}')
    s1.dpctl('mod-flows', f'ip,nw_src=10.0.0.10,nw_dst=10.0.0.100,nw_dst=10.0.0.2,actions=output:{rrh_port}')
    net.ping([ue2, vbbu2])

def run():
    topo = ComicranTopo()
    net = Mininet(topo=topo, controller=DefaultController, switch=OVSSwitch, link=TCLink, autoSetMacs=True)
    net.start()

    print("\n[INFO] COMIC-RAN demo with RRH as host started. Hosts: ue1, ue2, rrh, vbbu1, vbbu2")
    simulate_handover(net)
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()

