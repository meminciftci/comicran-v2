#!/usr/bin/python3

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSSwitch, DefaultController
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
import os
import time


UE_COUNT = 10  # total UEs

class ComicranTopo(Topo):
    def build(self):
        s1 = self.addSwitch('s1')

        # Core components
        rrh = self.addHost('rrh', ip='10.0.0.100')
        orch = self.addHost('orch', ip='10.0.0.200')

        self.vbbu_config = {
            "vbbu1": {"ip": "10.0.0.201", "port": 8080},
            "vbbu2": {"ip": "10.0.0.202", "port": 8081},
        }

        for name, info in self.vbbu_config.items():
            vbbu_host = self.addHost(name, ip=info["ip"])
            self.addLink(s1, vbbu_host)

        self.addLink(s1, rrh)
        self.addLink(s1, orch)

        root = self.addHost(
            'root', 
            ip='10.0.0.31/24',       # pick a subnet that doesn't conflict
            inNamespace=False
        )

        # link that host into your main switch
        self.addLink(root, s1)

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

def deploy_http_services(net, topo_vbbu_config):

    rrh = net.get('rrh')
    orch = net.get('orch')


    print("[INFO] Starting vBBU HTTP servers...")
    for name, info in topo_vbbu_config.items():
        vbbu_node = net.get(name)
        if(name == "vbbu1" or name == "vbbu2"):
            vbbu_node.cmd(f'python3 vbbu_server.py {info["port"]} &')
        else:
            vbbu_node.cmd(f'python3 vbbu_server.py {info["port"]} --inactive &')
        

    print("[INFO] Starting RRH HTTP proxy with dynamic routing control...")
    rrh.cmd('python3 rrh_proxy.py &')

    print("[INFO] Opening orchestrator terminal...")
    # orch.cmd('xterm -T orchestrator -e python3 orchestrator.py &')
    orch.cmd(
        'xterm -T orchestrator -e bash -lc "'
        'source ./venv/bin/activate && '
        'python3 orchestrator.py" &'
    )
    
    orch.cmd('sleep 2')

    print(f"[INFO] Launching {UE_COUNT} dynamic UE agents...")
    for i in range(1, UE_COUNT + 1):
        ue = net.get(f"ue{i}")
        ue.cmd(f'python3 ue_client.py 10.0.0.100 &')

    print("\n[INFO] ✅ All components launched")
    print("[INFO] 🧪 Dynamic UE traffic is active")
    print("[INFO] 🛰️  Use orchestrator to issue `handover` or `migrate` commands")
    print("[INFO] 🔍 Logs are in ../outputs/")


def cleanup():

    print("[INFO] Cleaning up processes...")
    os.system('pkill -f "python3 orchestrator.py"')
    print("[INFO] All processes terminated")

def run():
    clear_previous_logs()
    
    topo = ComicranTopo()
    net = Mininet(topo=topo, controller=DefaultController,
                  switch=OVSSwitch, link=TCLink, autoSetMacs=True)
    net.start()

    print("\n[INFO] COMIC-RAN HTTP application-layer demo started")
    deploy_http_services(net, topo.vbbu_config)

    try:
        CLI(net)
    finally:
        cleanup()
        net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
