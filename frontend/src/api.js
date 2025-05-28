// src/api.js
const API_BASE = process.env.REACT_APP_API_BASE || 'http://10.0.0.200:5006';

async function handleResponse(res) {
    if (!res.ok) {
      const err = await res.text();
      throw new Error(`${res.status}: ${err}`);
    }
    return res.json();
  }
  
  // UE Management
  export function addUEs(uids) {
    return fetch(`${API_BASE}/api/ue/add`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ uids }),
    }).then(handleResponse);
  }
  
  export function removeUEs(uids) {
    return fetch(`${API_BASE}/api/ue/remove`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ uids }),
    }).then(handleResponse);
  }
  
  export function listUEs() {
    return fetch(`${API_BASE}/api/ue/list`).then(handleResponse);
  }
  
  // Orchestrator actions
  export function handover(ue_id, target_vbbu) {
    return fetch(`${API_BASE}/api/handover`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ue_id, target_vbbu }),
    }).then(handleResponse);
  }
  
  export function migrate(source_vbbu, deactivate = false) {
    return fetch(`${API_BASE}/api/migrate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source_vbbu, deactivate }),
    }).then(handleResponse);
  }
  
  export function activateVBBU(vbbu) {
    return fetch(`${API_BASE}/api/vbbu/activate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ vbbu }),
    }).then(handleResponse);
  }
  
  export function deactivateVBBU(vbbu) {
    return fetch(`${API_BASE}/api/vbbu/deactivate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ vbbu }),
    }).then(handleResponse);
  }
  
  // Monitoring endpoints
  export function getAssignments() {
    return fetch(`${API_BASE}/api/assignments`).then(handleResponse);
  }
  
  export function getLoads() {
    return fetch(`${API_BASE}/api/loads`).then(handleResponse);
  }
  
  export function getVBBUs() {
    return fetch(`${API_BASE}/api/vbbus`).then(handleResponse);
  }
  