## Step 1
```
sudo apt update
sudo apt install mininet
sudo mn --test pingall
```

## Step 2
```
sudo apt install openvswitch-switch openvswitch-testcontroller
sudo apt install python3-pip
pip3 install networkx
```

## Step 3
```
sudo python3 comicran_mininet_demo.py
pingall
```

## Step 4 (inside the mininet terminal)
```
xterm vbbu1 vbbu2 rrh ue1 ue2
```

## Step 5 

Node: vbbu1 (running virtual base band unit 1 on port 8080)
```
python3 vbbu_server.py 8080 
```
Node: vbbu2 (running virtual base band unit 2 on port 8081)
```
python3 vbbu_server.py 8081 
```
Node: rrh (running remote radio head with the IP 10.0.0.100)
```
python3 rrh_proxy.py
```
Node: ue1 (running user equipment 1 with the connection to rrh IP)
```
python3 ue_client.py 10.0.0.100
```
Node: ue1 (running user equipment 2 with the connection to rrh IP, the same as ue1)
```
python3 ue_client.py 10.0.0.100
```

## Step 6




