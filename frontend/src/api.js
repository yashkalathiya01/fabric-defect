/**
 * Fabric AI Inspection System - API Client Helper
 */

export const API_BASE = "http://localhost:8000";

export async function fetchHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    if (res.ok) return await res.json();
  } catch (err) {
    // fallback check root /health
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (res.ok) return await res.json();
    } catch {}
  }
  return null;
}

export async function fetchDashboardMetrics() {
  const res = await fetch(`${API_BASE}/api/dashboard/metrics`);
  if (!res.ok) throw new Error("Failed to fetch dashboard metrics");
  return await res.json();
}

export async function fetchInspections(limit = 100) {
  const res = await fetch(`${API_BASE}/api/inspections?limit=${limit}`);
  if (!res.ok) throw new Error("Failed to fetch inspections");
  return await res.json();
}

export async function fetchInspectionDetail(id) {
  const res = await fetch(`${API_BASE}/api/inspections/${id}`);
  if (!res.ok) throw new Error(`Failed to load inspection ${id}`);
  return await res.json();
}

export async function inspectFabric(formData) {
  const res = await fetch(`${API_BASE}/api/inspect`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Inspection pipeline failed");
  }
  return await res.json();
}

export async function rethresholdInspection(inspectionId, threshold) {
  const formData = new FormData();
  formData.append("confidence_threshold", threshold.toString());
  const res = await fetch(`${API_BASE}/api/inspections/${inspectionId}/rethreshold`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to adjust confidence threshold");
  }
  return await res.json();
}

export async function clearAllInspections() {
  const res = await fetch(`${API_BASE}/api/inspections`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to clear inspection archive");
  }
  return await res.json();
}

export async function deleteInspection(inspectionId) {
  const res = await fetch(`${API_BASE}/api/inspections/${inspectionId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to delete inspection ${inspectionId}`);
  }
  return await res.json();
}

