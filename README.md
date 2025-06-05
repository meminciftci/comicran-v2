## 📁 Project Structure

```
.
├── frontend/                    # Web dashboard (React + Next.js)
├── mininet_topo/               # All Python components (simulated network)
│   ├── homicran_mininet_demo.py   # Launches full Mininet topology and services
│   ├── orchestrator.py
│   ├── rrh_proxy.py
│   ├── vbbu_server.py
│   ├── ue_client.py
│   ├── requirements.txt
│   ├── venv/                   # Python virtual environment
│
├── outputs/                    # Logs from orchestrator, RRH, UEs, and vBBUs
│   ├── orch_output.txt
│   ├── rrh_output.txt
│   ├── ue{1..10}_output.txt
│   ├── vbbu1_output.txt
│   ├── vbbu2_output.txt
│
├── toDo.txt                    # Development notes
```

---

## 🛠️ Setup Instructions

### 1. Setup Python Virtual Environment

```bash
cd mininet_topo
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

> Ensure you have Mininet installed and working (`sudo mn --test pingall` to verify).

---

## 🚀 Running the Simulation

### 1. Launch the Mininet Topology

```bash
sudo python3 homicran_mininet_demo.py
```

This will:
- Start Mininet switch topology
- Launch orchestrator, RRH, 2 vBBUs, and 10 UEs
- Open terminals (or subprocesses) for each component

> All logs are written to the `outputs/` directory automatically.

---

### 2. Start the Web Dashboard

```bash
cd frontend
npm install
npm run dev
```

Visit the dashboard at: [http://localhost:3000](http://localhost:3000)

---

## 🧠 Components Overview

- **Orchestrator** (`orchestrator.py`)  
  Flask-based controller that handles handovers, migrations, and system state.

- **RRH Proxy** (`rrh_proxy.py`)  
  Forwards UE traffic to the correct vBBU based on assignments.

- **vBBU Simulators** (`vbbu_server.py`)  
  Mimic BBU behavior. `vbbu1` is active by default, `vbbu1-prime` and `vbbu2` can be activated later.

- **UE Clients** (`ue_client.py`)  
  Simulated user devices sending periodic HTTP requests to RRH.

---

## 🧾 Output Logs

Logs are stored in the `outputs/` folder:

- `orch_output.txt`: Orchestrator log
- `rrh_output.txt`: RRH forwarding log
- `vbbu1_output.txt`, `vbbu2_output.txt`: vBBU activity logs
- `ue1_output.txt` – `ue10_output.txt`: Individual UE request logs

These help trace handovers, load migrations, and traffic behavior.

---

## 📡 REST API Endpoints

Available at `localhost:5006` from the orchestrator:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | `/api/ue/add`       | Connect UE to the system |
| POST   | `/api/ue/remove`    | Disconnect UE |
| POST   | `/api/ue/handover`  | Redirect a UE to a different vBBU |
| POST   | `/api/migrate`      | Mass-migrate all UEs to a new vBBU |
| POST   | `/api/vbbu/activate`   | Start a standby vBBU |
| POST   | `/api/vbbu/deactivate` | Shut down a vBBU |
| GET    | `/api/assignments`  | List current UE→vBBU mappings |
| GET    | `/api/loads`        | Show vBBU load info |
| GET    | `/api/vbbus`        | Show vBBU status and config |

---

## 🧭 Manual Control

You can use either:
- the **web dashboard** to trigger actions, or
- the **orchestrator CLI** (opened in a terminal window) for direct command-line operations.

---

## 🧩 Features

- Per-UE handover and migration simulation
- RRH-based traffic redirection
- Modular HTTP-based architecture
- Logs for traceability
- Frontend dashboard for real-time visualization

---

## 📌 Notes

- There is no real radio interface — all communication is over HTTP.
- vBBUs are simulated Python servers, not real containers (yet).
- All actions are triggered manually via dashboard or CLI.
- The `venv/` folder is local to `mininet_topo/` and should be activated before launching.

---

## 🧪 Tested On

- Ubuntu 20.04 / 22.04
- Python 3.10
- Node.js 18+
- Mininet 2.3.0

---

## 👨‍💻 Authors

- Furkan Şenkal  
- Muhammet Emin Çiftçi  
Advisor: Prof. Tuna Tuğcu

---

## 📄 License

This project is intended for academic use only.
