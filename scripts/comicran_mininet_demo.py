#!/usr/bin/python3

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSSwitch, DefaultController
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
import time
import os

UE_COUNT = 10  # total UEs

class ComicranTopo(Topo):
    def build(self):
        s1 = self.addSwitch('s1')

        # Core components
        rrh = self.addHost('rrh', ip='10.0.0.100')
        vbbu1 = self.addHost('vbbu1', ip='10.0.0.201')
        vbbu2 = self.addHost('vbbu2', ip='10.0.0.202')
        orch = self.addHost('orch', ip='10.0.0.200')

        self.addLink(s1, rrh)
        self.addLink(s1, vbbu1)
        self.addLink(s1, vbbu2)
        self.addLink(s1, orch)

        # Add dynamic UEs
        for i in range(1, UE_COUNT + 1):
            ue = self.addHost(f'ue{i}', ip=f'10.0.0.{i}')
            self.addLink(s1, ue)

def clear_previous_logs():
    output_dir = "../outputs"
    if os.path.exists(output_dir):
        for file in os.listdir(output_dir):
            file_path = os.path.join(output_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"[!] Failed to remove {file_path}: {e}")
    else:
        os.makedirs(output_dir)

def deploy_http_services(net):
    vbbu1 = net.get('vbbu1')
    vbbu2 = net.get('vbbu2')
    rrh = net.get('rrh')
    orch = net.get('orch')

    print("[INFO] Starting vBBU HTTP servers...")
    vbbu1.cmd('python3 vbbu_server.py 8080 &')
    vbbu2.cmd('python3 vbbu_server.py 8081 &')

    print("[INFO] Starting RRH HTTP proxy with dynamic routing control...")
    rrh.cmd('python3 rrh_proxy.py &')

    print("[INFO] Opening orchestrator terminal...")
    orch.cmd('xterm -T orchestrator -e python3 orchestrator.py &')

    print("[INFO] Opening user manager terminal...")
    orch.cmd('xterm -T user_manager -e python3 user_manager.py &')

    time.sleep(2)

    print(f"[INFO] Launching {UE_COUNT} dynamic UE agents...")
    for i in range(1, UE_COUNT + 1):
        ue = net.get(f"ue{i}")
        ue.cmd(f'python3 ue_client.py 10.0.0.100 &')

    print("\n[INFO] ✅ All components launched")
    print("[INFO] 🧪 Use user_manager to add/remove UEs")
    print("[INFO] 🛰️  Use orchestrator to issue `handover` or `migrate` commands")
    print("[INFO] 🔍 Logs are in /tmp/ and ../outputs/")

def cleanup():
    print("[INFO] Cleaning up processes...")
    # Kill orchestrator process
    os.system('pkill -f "python3 orchestrator.py"')
    # Kill user manager process
    os.system('pkill -f "python3 user_manager.py"')
    print("[INFO] All processes terminated")

def run():
    clear_previous_logs()
    
    topo = ComicranTopo()
    net = Mininet(topo=topo, controller=DefaultController,
                  switch=OVSSwitch, link=TCLink, autoSetMacs=True)
    net.start()

    print("\n[INFO] COMIC-RAN HTTP application-layer demo started")
    deploy_http_services(net)

    try:
        CLI(net)
    finally:
        cleanup()
        net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
