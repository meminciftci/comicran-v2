// src/App.js
import React, { useState, useEffect } from 'react';
import {
  addUEs, removeUEs, listUEs,
  handover, migrate, activateVBBU, deactivateVBBU,
  getAssignments, getLoads, getVBBUs
} from './api';

function App() {
  const [ueStates, setUEStates]       = useState({});
  const [assignments, setAssign]     = useState({});
  const [loads, setLoads]            = useState({});
  const [vbbus, setVBBUs]            = useState({});
  const [inputUEs, setInputUEs]      = useState('');
  const [handoverUE, setHandoverUE]  = useState('');
  const [targetVBBU, setTargetVBBU]  = useState('');

  // Load initial data
  useEffect(() => {
    listUEs().then(setUEStates);
    getAssignments().then(setAssign);
    getLoads().then(setLoads);
    getVBBUs().then(setVBBUs);
  }, []);

  const refreshUEs = () => listUEs().then(setUEStates);

  // Handlers
  const onAddUEs = async () => {
    const uids = inputUEs.split(',').map(x=>+x);
    await addUEs(uids);
    refreshUEs();
  };
  const onRemoveUEs = async () => {
    const token = inputUEs.trim() === 'all' ? 'all' : inputUEs.split(',').map(x=>+x);
    await removeUEs(token);
    refreshUEs();
  };
  const onHandover = async () => {
    await handover(handoverUE, targetVBBU);
    getAssignments().then(setAssign);
  };
  const onMigrate = async () => {
    await migrate(targetVBBU, false);
    getAssignments().then(setAssign);
    getVBBUs().then(setVBBUs);
  };
  const onActivate = async () => {
    await activateVBBU(targetVBBU);
    getVBBUs().then(setVBBUs);
  };
  const onDeactivate = async () => {
    await deactivateVBBU(targetVBBU);
    getVBBUs().then(setVBBUs);
  };

  return (
    <div style={{ padding: 20, fontFamily: 'sans-serif' }}>
      <h1>COMIC-RAN Dashboard</h1>

      <section>
        <h2>UE Connection State</h2>
        <pre>{JSON.stringify(ueStates, null, 2)}</pre>
        <input
          placeholder="e.g. 1,2,3 or all"
          value={inputUEs}
          onChange={e => setInputUEs(e.target.value)}
        />
        <button onClick={onAddUEs}>Connect UEs</button>
        <button onClick={onRemoveUEs}>Disconnect UEs</button>
      </section>

      <hr/>

      <section>
        <h2>UE → vBBU Assignments</h2>
        <pre>{JSON.stringify(assignments, null, 2)}</pre>
        <input
          placeholder="UE1"
          value={handoverUE}
          onChange={e => setHandoverUE(e.target.value)}
        />
        <input
          placeholder="vbbu2"
          value={targetVBBU}
          onChange={e => setTargetVBBU(e.target.value)}
        />
        <button onClick={onHandover}>Handover</button>
      </section>

      <hr/>

      <section>
        <h2>vBBU Management</h2>
        <pre>{JSON.stringify(vbbus, null, 2)}</pre>
        <input
          placeholder="vbbu3"
          value={targetVBBU}
          onChange={e => setTargetVBBU(e.target.value)}
        />
        <button onClick={onMigrate}>Migrate</button>
        <button onClick={onActivate}>Activate</button>
        <button onClick={onDeactivate}>Deactivate</button>
      </section>

      <hr/>

      <section>
        <h2>vBBU Loads</h2>
        <pre>{JSON.stringify(loads, null, 2)}</pre>
      </section>
    </div>
  );
}

export default App;
