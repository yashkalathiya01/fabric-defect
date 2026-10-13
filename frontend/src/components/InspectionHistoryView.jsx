import React, { useState, useEffect } from "react";
import {
  History,
  Search,
  FileDown,
  ArrowRight,
  Filter,
  Clock,
  Layers,
  Award,
  RefreshCw,
  Trash2,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";

import { API_BASE, fetchInspections, clearAllInspections, deleteInspection } from "../api";

export default function InspectionHistoryView({
  onSelectInspection,
  onHistoryCleared,
  onInspectionDeleted,
}) {
  const [inspections, setInspections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedGrade, setSelectedGrade] = useState("all");
  const [showClearModal, setShowClearModal] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [actionNotification, setActionNotification] = useState(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const data = await fetchInspections(100);
      setInspections(data.inspections || []);
    } catch (err) {
      console.error("Failed to fetch inspection history:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSingle = async (inspectionId) => {
    if (!window.confirm(`Permanently delete inspection record for Lot ID: ${inspectionId}?`)) {
      return;
    }
    setDeletingId(inspectionId);
    try {
      await deleteInspection(inspectionId);
      setInspections((prev) => prev.filter((item) => item.inspection_id !== inspectionId));
      if (onInspectionDeleted) {
        onInspectionDeleted(inspectionId);
      }
      setActionNotification({
        type: "success",
        message: `Inspection record ${inspectionId} has been deleted.`,
      });
      setTimeout(() => setActionNotification(null), 4000);
    } catch (err) {
      console.error("Failed to delete inspection:", err);
      setActionNotification({
        type: "error",
        message: err.message || "Failed to delete record.",
      });
      setTimeout(() => setActionNotification(null), 4000);
    } finally {
      setDeletingId(null);
    }
  };

  const handleExecuteClearAll = async () => {
    setClearing(true);
    try {
      const res = await clearAllInspections();
      setInspections([]);
      setShowClearModal(false);
      if (onHistoryCleared) {
        onHistoryCleared();
      }
      setActionNotification({
        type: "success",
        message: res.message || "All historical inspection records have been cleared.",
      });
      setTimeout(() => setActionNotification(null), 4000);
    } catch (err) {
      console.error("Failed to clear all inspections:", err);
      setActionNotification({
        type: "error",
        message: err.message || "Failed to clear inspection archive.",
      });
      setTimeout(() => setActionNotification(null), 4000);
    } finally {
      setClearing(false);
    }
  };

  const filtered = inspections.filter((insp) => {
    const matchesSearch =
      insp.inspection_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (insp.image_filename && insp.image_filename.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesGrade = selectedGrade === "all" || (insp.grade && insp.grade.toUpperCase() === selectedGrade);
    return matchesSearch && matchesGrade;
  });

  const gradeChipMap = {
    A: "chip-status-pass",
    B: "chip-status-steel",
    C: "chip-status-warn",
    D: "chip-status-fail",
    INVALID: "chip-status-fail",
  };

  return (
    <div className="space-y-4">
      
      {/* Header Bar */}
      <div className="panel-enterprise p-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-[#525252]">
              AUDIT DATABASE
            </span>
            <span className="text-[#DCDCDC]">/</span>
            <span className="text-xs text-[#737373]">
              ISO 9001 QUALITY RECORDS REPOSITORY
            </span>
          </div>
          <h2 className="text-sm font-bold text-[#171717] tracking-tight mt-0.5">
            Specimen Inspection Archive ({inspections.length} Historical Lots)
          </h2>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchHistory}
            className="px-3 py-1.5 rounded-lg bg-[#F5F5F5] hover:bg-[#EAEAEA] text-[#171717] border border-[#DCDCDC] text-xs font-medium flex items-center gap-1.5 transition-colors shadow-2xs cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Synchronize</span>
          </button>

          <button
            onClick={() => setShowClearModal(true)}
            disabled={inspections.length === 0 || loading}
            className="px-3 py-1.5 rounded-lg bg-[#F5F5F5] hover:bg-[#FCE8E6] text-[#C5221F] border border-[#FAD2CF] text-xs font-medium flex items-center gap-1.5 transition-colors disabled:opacity-40 disabled:cursor-not-allowed shadow-2xs cursor-pointer"
            title="Permanently clear all historical inspection records"
          >
            <Trash2 className="w-3.5 h-3.5 text-[#C5221F]" />
            <span>Clear All Inspections</span>
          </button>
        </div>
      </div>

      {/* Operation Status Notification Banner */}
      {actionNotification && (
        <div
          className={`p-3.5 rounded-xl border text-xs flex items-center justify-between transition-all ${
            actionNotification.type === "success"
              ? "bg-[#EAEAEA] text-[#137333] border-[#CEEAD6]"
              : "bg-[#FCE8E6] text-[#C5221F] border-[#FAD2CF]"
          }`}
        >
          <div className="flex items-center gap-2 font-medium">
            {actionNotification.type === "success" ? (
              <CheckCircle2 className="w-4 h-4 text-[#137333]" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-[#C5221F]" />
            )}
            <span>{actionNotification.message}</span>
          </div>
          <button
            onClick={() => setActionNotification(null)}
            className="text-xs opacity-70 hover:opacity-100 font-bold px-1.5 py-0.5 cursor-pointer"
          >
            ✕
          </button>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="panel-enterprise p-3 flex flex-wrap items-center justify-between gap-3">
        <div className="relative flex-1 min-w-[260px]">
          <Search className="w-3.5 h-3.5 text-[#737373] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Filter by Specimen Lot ID or source filename..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#EAEAEA] border border-[#DCDCDC] rounded-lg pl-8 pr-3 py-1.5 text-xs text-[#171717] placeholder-[#737373] focus:outline-none focus:bg-[#F5F5F5] focus:border-[#171717] transition-all"
          />
        </div>

        <div className="flex items-center gap-1 text-xs">
          <span className="text-[#525252] text-[11px] font-medium mr-1 uppercase">GRADE:</span>
          {["all", "A", "B", "C", "D", "INVALID"].map((g) => (
            <button
              key={g}
              onClick={() => setSelectedGrade(g)}
              className={`px-2.5 py-1 rounded-md text-[11px] uppercase transition-all font-medium border cursor-pointer ${
                selectedGrade === g
                  ? "bg-[#171717] text-[#F5F5F5] border-[#171717] shadow-2xs"
                  : "bg-[#F5F5F5] text-[#525252] border-[#DCDCDC] hover:text-[#171717] hover:bg-[#EAEAEA]"
              }`}
            >
              {g}
            </button>
          ))}
        </div>
      </div>

      {/* History Table */}
      <div className="panel-enterprise p-0 overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-[#525252] text-xs font-mono space-y-2">
            <RefreshCw className="w-5 h-5 animate-spin text-[#171717] mx-auto" />
            <p>Retrieving database records...</p>
          </div>
        ) : filtered.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="table-industrial">
              <thead>
                <tr>
                  <th>LOT ID</th>
                  <th>TIMESTAMP</th>
                  <th>ANOMALIES</th>
                  <th>WEAVE VECTOR (θv / θh)</th>
                  <th>QUALITY INDEX</th>
                  <th>DISPOSITION</th>
                  <th className="text-right">ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((insp) => {
                  const g = insp.grade || "D";
                  const chipClass = gradeChipMap[g] || "chip-status-neutral";

                  return (
                    <tr key={insp.inspection_id}>
                      <td className="font-bold text-[#171717]">
                        {insp.inspection_id}
                      </td>
                      <td className="text-[#525252]">
                        {insp.timestamp ? insp.timestamp.replace("T", " ").slice(0, 19) : "--"}
                      </td>
                      <td>
                        <span className={`px-2 py-0.5 rounded-full border text-[11px] font-mono ${
                          insp.total_defects > 0
                            ? "bg-[#FCE8E6] text-[#C5221F] border-[#FAD2CF] font-semibold"
                            : "bg-[#EAEAEA] text-[#333333] border-[#DCDCDC]"
                        }`}>
                          {insp.total_defects} defect{insp.total_defects === 1 ? "" : "s"}
                        </span>
                      </td>
                      <td className="text-[#333333]">
                        {insp.warp_angle !== null && insp.warp_angle !== undefined ? `${insp.warp_angle.toFixed(1)}°` : "--"} /{" "}
                        {insp.weft_angle !== null && insp.weft_angle !== undefined ? `${insp.weft_angle.toFixed(1)}°` : "--"}
                      </td>
                      <td className="font-bold text-[#171717]">
                        {insp.quality_score ? `${insp.quality_score.toFixed(1)} / 100` : "--"}
                      </td>
                      <td>
                        <span className={`chip-status ${chipClass}`}>
                          {g === "INVALID" ? "QUARANTINE" : `GRADE ${g}`}
                        </span>
                      </td>
                      <td className="text-right space-x-1.5">
                        {/* Download PDF button */}
                        <a
                          href={`${API_BASE}/api/report/${insp.inspection_id}`}
                          download
                          target="_blank"
                          rel="noreferrer"
                          className="p-1.5 rounded-lg bg-[#F5F5F5] hover:bg-[#EAEAEA] text-[#525252] hover:text-[#171717] border border-[#DCDCDC] inline-flex items-center transition-colors shadow-2xs"
                          title="Download ISO Inspection Report PDF"
                        >
                          <FileDown className="w-3.5 h-3.5" />
                        </a>
                        {/* View in Studio button */}
                        <button
                          onClick={() => onSelectInspection(insp.inspection_id)}
                          className="px-2.5 py-1 rounded-lg bg-[#EAEAEA] hover:bg-[#E2E2E2] text-[#171717] border border-[#DCDCDC] text-xs font-semibold inline-flex items-center gap-1 transition-colors cursor-pointer"
                          title="Open full inspection in workbench"
                        >
                          <span>Inspect</span>
                          <ArrowRight className="w-3 h-3 text-[#525252]" />
                        </button>
                        {/* Delete Single Inspection button */}
                        <button
                          onClick={() => handleDeleteSingle(insp.inspection_id)}
                          disabled={deletingId === insp.inspection_id}
                          className="p-1.5 rounded-lg bg-[#F5F5F5] hover:bg-[#FCE8E6] text-[#737373] hover:text-[#C5221F] border border-[#DCDCDC] hover:border-[#FAD2CF] inline-flex items-center transition-colors disabled:opacity-40 shadow-2xs cursor-pointer"
                          title="Delete this inspection record"
                        >
                          {deletingId === insp.inspection_id ? (
                            <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#C5221F]" />
                          ) : (
                            <Trash2 className="w-3.5 h-3.5" />
                          )}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-16 text-center text-[#525252] text-xs font-mono space-y-2">
            <History className="w-6 h-6 text-[#737373] mx-auto opacity-50" />
            <h4 className="text-[#171717] font-semibold text-sm">No Matching Specimen Records</h4>
            <p className="text-[#525252]">Scan a lot sample or clear search query to populate archive.</p>
          </div>
        )}
      </div>

      {/* Purge All Inspections Confirmation Modal */}
      {showClearModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs">
          <div className="bg-[#F5F5F5] max-w-md w-full p-6 space-y-4 border border-[#DCDCDC] shadow-2xl animate-in fade-in zoom-in-95 rounded-2xl">
            <div className="flex items-start gap-3">
              <div className="p-2.5 rounded-xl bg-[#FCE8E6] text-[#C5221F] border border-[#FAD2CF]">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-bold text-[#171717] tracking-tight">
                  Purge Inspection Archive
                </h3>
                <p className="text-xs text-[#525252] leading-relaxed">
                  Are you sure you want to permanently delete all{" "}
                  <strong className="text-[#171717] font-mono">{inspections.length}</strong> previous
                  inspection records, defect bounding box telemetry, and generated PDF reports?
                </p>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-[#FCE8E6] border border-[#FAD2CF] text-xs text-[#C5221F] flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[#C5221F]"></span>
              <span>This database action is irreversible.</span>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#DCDCDC]">
              <button
                type="button"
                onClick={() => setShowClearModal(false)}
                disabled={clearing}
                className="px-3.5 py-2 rounded-lg bg-[#F5F5F5] hover:bg-[#EAEAEA] text-[#333333] border border-[#DCDCDC] text-xs font-medium transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleExecuteClearAll}
                disabled={clearing}
                className="px-4 py-2 rounded-lg bg-[#C5221F] hover:bg-[#A51D24] text-[#F5F5F5] font-semibold text-xs flex items-center gap-1.5 transition-colors shadow-xs disabled:opacity-50 cursor-pointer"
              >
                {clearing ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Purging Records...</span>
                  </>
                ) : (
                  <>
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Confirm & Purge All</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
