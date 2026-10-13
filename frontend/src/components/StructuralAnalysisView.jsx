import React, { useState } from "react";
import {
  Compass,
  Layers,
  Activity,
  CheckCircle,
  AlertCircle,
  Info,
  Maximize2,
  GitCommit,
  RotateCw,
  ShieldAlert,
} from "lucide-react";

import { API_BASE } from "../api";

export default function StructuralAnalysisView({ inspection }) {
  const [activeStage, setActiveStage] = useState("canny_edges");

  if (!inspection) {
    return (
      <div className="panel-enterprise p-12 text-center space-y-4">
        <AlertCircle className="w-10 h-10 text-amber-600 mx-auto opacity-80" />
        <h3 className="text-base font-semibold text-[#171717]">No Structural Data Available</h3>
        <p className="text-xs text-[#525252]">Perform a specimen inspection to extract yarn weave telemetry.</p>
      </div>
    );
  }

  const struct = inspection.structural_analysis || {};
  const warpAngle = struct.warp_angle;
  const weftAngle = struct.weft_angle;
  const alignDev = struct.alignment_deviation;
  const warpSpacing = struct.warp_spacing;
  const weftSpacing = struct.weft_spacing;
  const warpStd = struct.warp_spacing_std;
  const weftStd = struct.weft_spacing_std;
  const confidence = struct.orientation_confidence || 0;

  const visUrls = struct.visualization_urls || {};

  const stages = [
    { id: "canny_edges", label: "Canny Edge Contours", desc: "Bi-threshold gradient magnitude operator isolating inter-yarn boundaries", key: "canny_edges" },
    { id: "threshold", label: "Adaptive Threshold", desc: "Local neighborhood intensity binarization highlighting micro-apertures", key: "threshold" },
    { id: "grayscale", label: "Grayscale Luminance", desc: "Normalized single-channel 8-bit luminance representation (0.299R + 0.587G + 0.114B)", key: "grayscale" },
  ];

  const currentStage = stages.find((s) => s.id === activeStage) || stages[0];
  const currentImgUrl = visUrls[currentStage.key]
    ? `${API_BASE}${visUrls[currentStage.key]}`
    : null;

  return (
    <div className="space-y-2.5">
      
      {/* Specimen Non-Fabric Quarantine Warning */}
      {inspection.quality?.grade === "INVALID" && (
        <div className="px-3.5 py-2.5 rounded-xl border border-red-200 bg-red-50 text-xs flex items-center gap-3 font-mono">
          <ShieldAlert className="w-4 h-4 flex-shrink-0 text-red-600" />
          <div className="text-red-700">
            <span className="font-bold uppercase">Structural Telemetry Bypassed: </span>
            Specimen domain authentication rejected (invalid photo). Yarn alignment metrics suppressed.
          </div>
        </div>
      )}
      
      {/* Compact Top Header Bar */}
      <div className="panel-enterprise px-4 py-2.5 flex flex-wrap items-center justify-between gap-2">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono font-semibold text-[#525252]">
              OPENCV IMAGE PROCESSING
            </span>
            <span className="text-[#A3A3A3]">/</span>
            <span className="text-[11px] font-mono text-[#525252]">
              CONTOUR, THRESHOLD & LUMINANCE PIPELINE
            </span>
          </div>
          <h2 className="text-sm font-semibold text-[#171717] tracking-tight">
            Canny Edge Contours, Adaptive Threshold & Grayscale Luminance
          </h2>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <div className="px-2.5 py-1 bg-[#EAEAEA] border border-[#DCDCDC] rounded-lg flex items-center gap-2">
            <span className="text-[#525252]">ACTIVE FILTER:</span>
            <span className="font-bold text-[#171717]">{currentStage.label.toUpperCase()}</span>
          </div>
        </div>
      </div>

      {/* Main Structural Stage Pipeline (Compact Single-Screen Fit) */}
      <div className="panel-enterprise p-3 space-y-2.5">
        
        {/* Unified Stage Selector & Description Bar */}
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#DCDCDC] pb-2.5">
          <div className="flex flex-wrap gap-1.5">
            {stages.map((s) => (
              <button
                key={s.id}
                onClick={() => setActiveStage(s.id)}
                className={`px-3 py-1 rounded-lg text-xs font-mono transition-colors border ${
                  activeStage === s.id
                    ? "bg-[#171717] text-[#F5F5F5] font-medium border-[#171717] shadow-xs"
                    : "bg-[#F5F5F5] text-[#525252] border-[#DCDCDC] hover:bg-[#EAEAEA] hover:text-[#171717]"
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2 text-xs font-mono bg-[#EAEAEA] px-3 py-1 rounded-lg border border-[#DCDCDC]">
            <span className="text-[#171717] font-semibold">STAGE: {currentStage.label}</span>
            <span className="text-[#A3A3A3]">|</span>
            <span className="text-[#525252] text-[11px]">{currentStage.desc}</span>
          </div>
        </div>

        {/* Viewport-Fitted Stage Canvas (No Scroll Required) */}
        <div className="relative h-[calc(100vh-225px)] min-h-[280px] max-h-[460px] w-full bg-[#EAEAEA] border border-[#DCDCDC] rounded-xl overflow-hidden flex items-center justify-center p-2">
          {currentImgUrl ? (
            <img
              src={currentImgUrl}
              alt={currentStage.label}
              className="max-w-full max-h-full w-auto h-full object-contain rounded"
            />
          ) : (
            <div className="text-center p-6 text-[#525252] text-xs font-mono">
              TRANSFORMATION STAGE BUFFER EMPTY
            </div>
          )}

          {/* Viewport Overlay */}
          <div className="absolute bottom-2 left-2 px-2.5 py-1 bg-[#F5F5F5]/95 border border-[#DCDCDC] rounded-md shadow-xs font-mono text-[10px] text-[#525252]">
            PIPELINE STEP: {currentStage.key.toUpperCase()}
          </div>
        </div>

      </div>

    </div>
  );
}
