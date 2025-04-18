#!/usr/bin/python3

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSSwitch, DefaultController
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
import os

class ComicranTopo(Topo):
    def build(self):
        s1 = self.addSwitch('s1')
        rrh = self.addHost('rrh', ip='10.0.0.100')
        vbbu1 = self.addHost('vbbu1', ip='10.0.0.10')
        vbbu2 = self.addHost('vbbu2', ip='10.0.0.20')
        ue1 = self.addHost('ue1', ip='10.0.0.1')
        ue2 = self.addHost('ue2', ip='10.0.0.2')

        self.addLink(s1, rrh)
        self.addLink(s1, ue1)
        self.addLink(s1, ue2)
        self.addLink(s1, vbbu1)
        self.addLink(s1, vbbu2)

def deploy_http_services(net):
    vbbu1 = net.get('vbbu1')
    vbbu2 = net.get('vbbu2')
    rrh = net.get('rrh')

    print("[INFO] Starting vBBU HTTP servers")
    vbbu1.cmd('python3 /home/mininet/vbbu_server.py 8080 > /tmp/vbbu1.log 2>&1 &')
    vbbu2.cmd('python3 /home/mininet/vbbu_server.py 8081 > /tmp/vbbu2.log 2>&1 &')

    print("[INFO] Starting RRH HTTP proxy with dynamic routing control")
    rrh.cmd('python3 /home/mininet/rrh_proxy.py > /tmp/rrh.log 2>&1 &')

    print("\n[INFO] ✅ HTTP services deployed")
    print("[INFO] 📡 Test with:")
    print("       xterm ue1 ue2 rrh")
    print("       python3 /home/mininet/ue_client.py 10.0.0.100")
    print("[INFO] 🔄 Switch vBBU from rrh terminal by typing 'vbbu1' or 'vbbu2'\n")

def run():
    topo = ComicranTopo()
    net = Mininet(topo=topo, controller=DefaultController, switch=OVSSwitch, link=TCLink, autoSetMacs=True)
    net.start()

    print("\n[INFO] COMIC-RAN HTTP application-layer demo started")
    deploy_http_services(net)

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()


