# app.py

from nicegui import ui
from orchestrator import OrchClient
import traceback

# ─── 1) Client & Static Config ────────────────────────────────────────────
client = OrchClient(host='127.0.0.1', port=9100, timeout=2)

ue_ids = [f'UE{i}' for i in range(1, 11)]
vbbu_config = {
    'vbbu1': ('10.0.0.201', 8080),
    'vbbu2': ('10.0.0.202', 8081),
    'vbbu3': ('10.0.0.203', 8082),
    'vbbu4': ('10.0.0.204', 8083),
    'vbbu5': ('10.0.0.205', 8084),
}

# ─── 2) Assignments Table ─────────────────────────────────────────────────────
table = ui.table(
    columns=[
        {'field': 'ue',   'label': 'UE'},
        {'field': 'vbbu','label': 'Assigned vBBU'}
    ],
    rows=[]
).style('width: 300px')   # make it a bit wider so you can actually read the text


# ─── 3) CPU/Connections Bar Chart ────────────────────────────────────────────
chart = ui.echart({
    'xAxis': { 'type': 'category', 'data': [] },
    'yAxis': { 'type': 'value' },
    'series': [
        { 'name': 'CPU',         'type': 'bar', 'data': [] },
        { 'name': 'Connections', 'type': 'bar', 'data': [] },
    ]
})

# ─── 4) Refresh Logic ─────────────────────────────────────────────────────────
def refresh():
    try:
        # — update assignments table —
        assigns = client.get_assignments()  
        table.rows = [
            {'ue': ue, 'vbbu': f"vBBU{info['vbbu_ip'].split(".")[-1][-1]}"}
            for ue, info in assigns.items()
        ]
        table.update()


        # — update loads chart —
        loads = client.get_loads()
        labels, cpu_data, conn_data = [], [], []
        for ip, info in loads.items():
            labels.append(ip.split('.')[-1])
            cpu_data.append(info.get('cpu', 0))
            conn_data.append(info.get('connections', 0))

        opts = chart.options
        opts['xAxis']['data']      = labels
        opts['series'][0]['data']  = cpu_data
        opts['series'][1]['data']  = conn_data
        chart.update()

    except Exception as e:
        # orchestrator might not be ready yet
        print('dashboard refresh error:', e)
        traceback.print_exc()

# one immediate fetch, then every 2 seconds
refresh()
ui.timer(2.0, refresh)

# ─── 5) Handover Form ─────────────────────────────────────────────────────────
with ui.row().style('margin-top:20px'):
    ue_select = ui.select(
        ue_ids, label='UE_ID', value='UE1'
    ).props('filterable use-input')

    vbbu_select = ui.select(
        list(vbbu_config.keys()), label='vBBU_NAME', value='vbbu1'
    ).props('filterable use-input')

    def on_handover():
        ue_id     = ue_select.value.strip().upper()
        vbbu_name = vbbu_select.value.strip()
        if vbbu_name not in vbbu_config:
            ui.notify(f"Unknown vBBU: {vbbu_name}", color='negative')
            return
        ip, port = vbbu_config[vbbu_name]
        try:
            result = client.handover(ue_id, ip, port)
            ui.notify(f"Handover result: {result}", color='positive')
        except Exception as e:
            ui.notify(f"Handover error: {e}", color='negative')

    ui.button('Handover', on_click=on_handover)

# ─── 6) Footer Counter ───────────────────────────────────────────────────────
ui.label().bind_text_from(
    table,
    'rows',
    lambda rows: f"Total UE assignments: {len(rows)}"
)

# ─── 7) Launch the Dashboard ─────────────────────────────────────────────────
ui.run(title='COMIC-RAN Dashboard', port=8085)
