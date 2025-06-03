const API_BASE = process.env.REACT_APP_API_BASE || 'http://10.0.0.200:5006';

async function handleResponse(res) {
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`${res.status}: ${err}`);
  }
  return res.json();
}

// UE Management
export async function addUEs(uids) {
  console.log('called',uids)
  const res = await fetch(`${API_BASE}/api/ue/add`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ uids }),
  });
  return handleResponse(res);
}

export async function removeUEs(uids) {
  const res = await fetch(`${API_BASE}/api/ue/remove`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ uids }),
  });
  return handleResponse(res);
}

export async function listUEs() {
  const res = await fetch(`${API_BASE}/api/ue/list`);
  return handleResponse(res);
}

// Orchestrator actions
export async function handover(ue_id, target_vbbu) {
  
  const res = await fetch(`${API_BASE}/api/handover`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ue_id, target_vbbu }),
  });
  console.log('handover',ue_id,target_vbbu,res.status)
  return handleResponse(res);
}

export async function migrate(source_vbbu, target_vbbu='vbbu1-prime', deactivate = false) {
  console.log('source', source_vbbu)
  const res = await fetch(`${API_BASE}/api/migrate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source_vbbu,target_vbbu, deactivate }),
  });
  return handleResponse(res);
}

export async function activateVBBU(vbbu) {
  const res = await fetch(`${API_BASE}/api/vbbu/activate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ vbbu }),
  });
  return handleResponse(res);
}

export async function deactivateVBBU(vbbu) {
  const res = await fetch(`${API_BASE}/api/vbbu/deactivate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ vbbu }),
  });
  return handleResponse(res);
}

// Monitoring endpoints
export async function getAssignments() {
  const res = await fetch(`${API_BASE}/api/assignments`);
  return handleResponse(res);
}

export async function getLoads() {
  const res = await fetch(`${API_BASE}/api/loads`);
  return handleResponse(res);
}

export async function getVBBUs() {
  const res = await fetch(`${API_BASE}/api/vbbus`);
  return handleResponse(res);
}
