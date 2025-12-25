/**
 * API client for CI Pipeline backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function fetchDashboard() {
  const response = await fetch(`${API_BASE_URL}/dashboard`);
  if (!response.ok) throw new Error('Failed to fetch dashboard');
  return response.json();
}

export async function fetchRuns(limit = 24, status = null) {
  let url = `${API_BASE_URL}/runs?limit=${limit}`;
  if (status) url += `&status=${status}`;
  const response = await fetch(url);
  if (!response.ok) throw new Error('Failed to fetch runs');
  return response.json();
}

export async function fetchRun(runId) {
  const response = await fetch(`${API_BASE_URL}/runs/${runId}`);
  if (!response.ok) throw new Error('Failed to fetch run');
  return response.json();
}

export async function fetchIncidents(status = null) {
  let url = `${API_BASE_URL}/incidents`;
  if (status) url += `?status=${status}`;
  const response = await fetch(url);
  if (!response.ok) throw new Error('Failed to fetch incidents');
  return response.json();
}

export async function fetchIncident(incidentId) {
  const response = await fetch(`${API_BASE_URL}/incidents/${incidentId}`);
  if (!response.ok) throw new Error('Failed to fetch incident');
  return response.json();
}

export async function fetchFlakyTests() {
  const response = await fetch(`${API_BASE_URL}/flaky-tests`);
  if (!response.ok) throw new Error('Failed to fetch flaky tests');
  return response.json();
}

export async function createRun(data) {
  const response = await fetch(`${API_BASE_URL}/runs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!response.ok) throw new Error('Failed to create run');
  return response.json();
}

