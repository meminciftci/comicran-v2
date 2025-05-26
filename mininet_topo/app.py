# app.py

from nicegui import ui
from orchestrator import OrchClient
import traceback

# ─── 1) Client & Static Config ────────────────────────────────────────────
client = OrchClient(host='127.0.0.1', port=9100, timeout=15)

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
        {'field': 'ue',   'label': 'UE', 'align': 'left'},
        {'field': 'vbbu','label': 'Assigned vBBU', 'align': 'left'}
    ],
    rows=[]
).style('width: 300px')


# ─── 3) CPU/Connections Bar Chart ────────────────────────────────────────────
chart = ui.echart({
    'title': { 'text': 'vBBU Loads' },
    'tooltip': { 'trigger': 'axis', 'axisPointer': { 'type': 'shadow' } },
    'legend': { 'data': ['CPU Usage', 'Active Connections'] },
    'grid': { 'left': '3%', 'right': '4%', 'bottom': '3%', 'containLabel': True },
    'xAxis': { 'type': 'category', 'data': [], 'axisLabel': { 'rotate': 45 } },
    'yAxis': [
        {
            'type': 'value',
            'name': 'CPU Usage (%)',
            'min': 0,
            'max': 100,
            'interval': 20,
            'axisLabel': { 'formatter': '{value} %' }
        },
        {
            'type': 'value',
            'name': 'Active Connections',
            'min': 0,
            'interval': 5,
            'axisLabel': { 'formatter': '{value}' }
        }
    ],
    'series': [
        {
            'name': 'CPU Usage',
            'type': 'bar',
            'yAxisIndex': 0,
            'data': [],
            'itemStyle': { 'color': '#5470C6' }
        },
        {
            'name': 'Active Connections',
            'type': 'bar',
            'yAxisIndex': 1,
            'data': [],
            'itemStyle': { 'color': '#91CC75' }
        }
    ]
})

# ─── 4) Refresh Logic ─────────────────────────────────────────────────────────
def refresh():
    try:


        # — update assignments table —
        assigns = client.get_assignments()
        table.rows = [
            {'ue': ue, 'vbbu': f"vBBU{info['vbbu_ip'].split('.')[-1][-1]}"}
            for ue, info in assigns.items()
        ]
        table.update()

        # — update loads chart —
        vbbus = client.get_vbbus()
        labels, cpu_data, conn_data = [], [], []
        for name, info in vbbus.items():
            if not info.get('is_active', False):
                continue
            labels.append(name)
            cpu_data.append(info.get('cpu', 0))
            conn_data.append(info.get('connections', 0))

        opts = chart.options
        opts['xAxis']['data']      = labels
        opts['series'][0]['data']  = cpu_data
        opts['series'][1]['data']  = conn_data
        chart.update()


    except Exception as e:
        print('Dashboard refresh error:', e)
        ui.notify(f"Dashboard refresh error: {e}", color='negative')
        traceback.print_exc()

ui.timer(2.0, refresh)

# ─── 5) Handover Form ─────────────────────────────────────────────────────────
with ui.row().style('margin-top:20px'):
    ui.label('Handover UE').classes('text-h6')
    ue_select = ui.select(
        ue_ids, label='UE_ID', value='UE1'
    ).props('filterable use-input')

    vbbu_select = ui.select(
        list(vbbu_config.keys()), label='Target vBBU', value='vbbu1'
    ).props('filterable use-input')

    async def on_handover():
        ue_id     = ue_select.value.strip().upper()
        vbbu_name = vbbu_select.value.strip()
        if vbbu_name not in vbbu_config:
            ui.notify(f"Unknown vBBU: {vbbu_name}", color='negative')
            return
        ip, port = vbbu_config[vbbu_name]
        try:
            result = client.handover(ue_id, ip, port)
            ui.notify(f"Handover result: {result}", color='positive')
            refresh()
        except Exception as e:
            ui.notify(f"Handover error: {e}", color='negative')

    ui.button('Perform Handover', on_click=on_handover)

# ─── 6) Other Orchestrator Functions ─────────────────────────────────────────
with ui.column().classes('q-gutter-md'):
    ui.label('Orchestrator Control').classes('text-h6')

    # Migrate Function (Simplified to match orchestrator's expectation)
    with ui.row():
            migrate_from_vbbu_select = ui.select(
                list(vbbu_config.keys()), label='Migrate UEs From vBBU', value='vbbu1'
            ).props('filterable use-input')

            async def on_migrate():
                vbbu_name = migrate_from_vbbu_select.value.strip()
                if vbbu_name not in vbbu_config:
                    ui.notify(f"Unknown source vBBU: {vbbu_name}", color='negative')
                    return

                # LOOKUP the IP:port for this vBBU name
                ip, port = vbbu_config[vbbu_name]
                from_vbbu = f"{ip}:{port}"

                try:
                    # send the fully-qualified from_vbbu
                    result = client.migrate(from_vbbu)
                    ui.notify(f"Migration initiated: {result}", color='positive')
                    refresh()
                except Exception as e:
                    ui.notify(f"Migration error: {e}", color='negative')

            ui.button('Initiate Migration', on_click=on_migrate)

    # Activate/Deactivate vBBU Functions
    with ui.row():
        control_vbbu_select = ui.select(
            list(vbbu_config.keys()), label='Control vBBU', value='vbbu1'
        ).props('filterable use-input')

        async def on_activate_vbbu():
            vbbu_name = control_vbbu_select.value.strip()
            if vbbu_name not in vbbu_config:
                ui.notify(f"Unknown vBBU: {vbbu_name}", color='negative')
                return
            ip, port = vbbu_config[vbbu_name]
            try:
                success = client.activate_vbbu(ip, port)
                if success:
                    ui.notify(f"vBBU {vbbu_name} activated successfully", color='positive')
                    refresh()
                else:
                    ui.notify(f"Failed to activate vBBU {vbbu_name}", color='negative')
            except Exception as e:
                ui.notify(f"Activation error: {e}", color='negative')

        async def on_deactivate_vbbu():
            vbbu_name = control_vbbu_select.value.strip()
            if vbbu_name not in vbbu_config:
                ui.notify(f"Unknown vBBU: {vbbu_name}", color='negative')
                return
            ip, port = vbbu_config[vbbu_name]
            try:
                success = client.deactivate_vbbu(ip, port)
                if success:
                    ui.notify(f"vBBU {vbbu_name} deactivated successfully", color='positive')
                    refresh()
                else:
                    ui.notify(f"Failed to deactivate vBBU {vbbu_name}", color='negative')
            except Exception as e:
                ui.notify(f"Deactivation error: {e}", color='negative')

        ui.button('Activate vBBU', on_click=on_activate_vbbu, color='green')
        ui.button('Deactivate vBBU', on_click=on_deactivate_vbbu, color='red')


# ─── 7) Footer Counter ───────────────────────────────────────────────────────
ui.label().bind_text_from(
    table,
    'rows',
    lambda rows: f"Total UE assignments: {len(rows)}"
).classes('q-mt-md')

# ─── 8) Launch the Dashboard ─────────────────────────────────────────────────
ui.run(host='0.0.0.0', title='COMIC-RAN Dashboard', port=8085)