import React from "react";
import { X, FileDown, ExternalLink, Printer, ShieldCheck } from "lucide-react";
import { API_BASE } from "../api";

export default function ReportModal({ inspectionId, isOpen, onClose }) {
  if (!isOpen || !inspectionId) return null;

  const pdfUrl = `${API_BASE}/api/report/${inspectionId}`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-900/60 backdrop-blur-xs animate-fadeIn">
      <div className="relative w-full max-w-5xl h-[88vh] rounded-2xl border border-[#DCDCDC] flex flex-col overflow-hidden shadow-2xl bg-[#F5F5F5]">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between p-4 px-6 border-b border-[#DCDCDC] bg-[#F5F5F5]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-[#EAEAEA] border border-[#DCDCDC] flex items-center justify-center text-[#171717]">
              <FileDown className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-[#171717]">
                Official Quality Certificate: <span className="font-mono text-[#525252] font-bold">{inspectionId}</span>
              </h3>
              <p className="text-xs text-[#737373]">ASTM D5430 / ISO 9001:2015 Conformance Report</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <a
              href={pdfUrl}
              download={`Fabric_Inspection_Report_${inspectionId}.pdf`}
              className="btn-enterprise-primary text-xs flex items-center gap-1.5"
            >
              <FileDown className="w-3.5 h-3.5" />
              <span>Download PDF</span>
            </a>

            <a
              href={pdfUrl}
              target="_blank"
              rel="noreferrer"
              className="p-2 rounded-lg bg-[#F5F5F5] hover:bg-[#EAEAEA] text-[#525252] border border-[#DCDCDC] text-xs flex items-center transition-colors"
              title="Open in external viewer"
            >
              <ExternalLink className="w-3.5 h-3.5" />
            </a>

            <button
              onClick={onClose}
              className="p-2 rounded-lg bg-[#F5F5F5] hover:bg-red-50 text-[#737373] hover:text-red-600 border border-[#DCDCDC] transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Modal Body: Embedded PDF Iframe */}
        <div className="flex-1 w-full bg-[#EAEAEA] relative">
          <iframe
            src={`${pdfUrl}#toolbar=1&navpanes=0`}
            title={`Report ${inspectionId}`}
            className="w-full h-full border-none"
          />
        </div>

      </div>
    </div>
  );
}
