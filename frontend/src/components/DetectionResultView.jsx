import React, { useState, useMemo } from "react";
import {
  Layers,
  Eye,
  FileDown,
  Compass,
  Award,
  AlertTriangle,
  CheckCircle,
  Sliders,
  RefreshCw,
  Save,
  Crosshair,
  Maximize2,
  Tag,
  Grid,
  ShieldAlert,
  ArrowRight,
} from "lucide-react";

import { API_BASE, rethresholdInspection } from "../api";

export default function DetectionResultView({
  inspection,
  onNavigateStructural,
  onNavigateQuality,
  onOpenReport,
  onInspectionUpdated,
}) {
  const initialThreshold = inspection?.model?.confidence_threshold || 0.50;
  const [threshold, setThreshold] = useState(initialThreshold);
  const [activeTab, setActiveTab] = useState("interactive"); // 'interactive' | 'server' | 'raw'
  const [selectedClassFilter, setSelectedClassFilter] = useState("all");
  const [hoveredBox, setHoveredBox] = useState(null);
  const [showCrosshair, setShowCrosshair] = useState(true);
  const [showLabels, setShowLabels] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");

  if (!inspection) {
    return (
      <div className="panel-enterprise p-12 text-center space-y-4">
        <AlertTriangle className="w-10 h-10 text-amber-600 mx-auto opacity-80" />
        <h3 className="text-base font-semibold text-[#171717]">No Specimen Inspection Loaded</h3>
        <p className="text-xs text-[#525252]">Select a record from the audit archive or initiate a new lot scan.</p>
      </div>
    );
  }

  const iid = inspection.inspection_id;
  const imgW = inspection.image?.width || 640;
  const imgH = inspection.image?.height || 640;

  const fabricVal = inspection.fabric_validation || { is_valid_fabric: true };
  const isFabricValid = fabricVal.is_valid_fabric !== false && inspection.quality?.grade !== "INVALID";

  // Candidate pool: either all_detections or detailed_boxes (suppressed completely if non-fabric)
  const candidates = useMemo(() => {
    if (!isFabricValid) return [];
    if (inspection.all_detections && inspection.all_detections.length > 0) {
      return inspection.all_detections;
    }
    return inspection.defect_analysis?.detailed_boxes || inspection.detections || [];
  }, [inspection, isFabricValid]);

  // Dynamically filter candidate detections by live threshold
  const activeDetections = useMemo(() => {
    if (!isFabricValid) return [];
    return candidates.filter((d) => parseFloat(d.confidence) >= threshold);
  }, [candidates, threshold, isFabricValid]);

  // Class filter
  const displayBoxes = useMemo(() => {
    if (!isFabricValid) return [];
    if (selectedClassFilter === "all") return activeDetections;
    return activeDetections.filter(
      (b) => b.class.toLowerCase() === selectedClassFilter.toLowerCase()
    );
  }, [activeDetections, selectedClassFilter, isFabricValid]);

  // Dynamically compute defect counts per class
  const liveCounts = useMemo(() => {
    const counts = { total: activeDetections.length, hole: 0, knot: 0, stain: 0 };
    if (!isFabricValid) return counts;
    for (const d of activeDetections) {
      const c = d.class.toLowerCase();
      if (counts[c] !== undefined) counts[c]++;
    }
    return counts;
  }, [activeDetections, isFabricValid]);

  // Dynamically compute Defect Score & Quality Score
  const { liveDefectScore, liveQualityScore, liveGrade } = useMemo(() => {
    if (!isFabricValid) {
      return {
        liveDefectScore: 0.0,
        liveQualityScore: 0.0,
        liveGrade: "INVALID",
      };
    }

    let defScore = 100.0;
    if (activeDetections.length > 0) {
      const countPenalty = (liveCounts.hole * 15.0) + (liveCounts.knot * 7.5) + (liveCounts.stain * 6.0);
      let totalArea = 0;
      for (const d of activeDetections) {
        const bbox = d.bbox || [0, 0, 0, 0];
        const w = Math.max(0, bbox[2] - bbox[0]);
        const h = Math.max(0, bbox[3] - bbox[1]);
        totalArea += w * h;
      }
      const areaPct = (totalArea / Math.max(1, imgW * imgH)) * 100.0;
      const areaPenalty = Math.min(40.0, areaPct * 15.0);
      defScore = Math.max(0.0, Math.min(100.0, 100.0 - countPenalty - areaPenalty));
    }

    const structScore = inspection.quality?.structure_score || 85.0;
    const qScore = Math.round((0.60 * defScore + 0.40 * structScore) * 10) / 10;

    let g = "D";
    if (qScore >= 90) g = "A";
    else if (qScore >= 75) g = "B";
    else if (qScore >= 60) g = "C";

    return {
      liveDefectScore: Math.round(defScore * 10) / 10,
      liveQualityScore: qScore,
      liveGrade: g,
    };
  }, [activeDetections, liveCounts, imgW, imgH, inspection, isFabricValid]);

  // Apply & Save to Database & PDF
  const handleApplyThreshold = async () => {
    if (!isFabricValid) return;
    setIsSaving(true);
    setSaveMessage("");
    try {
      const updated = await rethresholdInspection(iid, threshold);
      if (onInspectionUpdated) onInspectionUpdated(updated);
      setSaveMessage("Threshold saved & PDF updated.");
      setTimeout(() => setSaveMessage(""), 4000);
    } catch (err) {
      setSaveMessage(`Error: ${err.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  const effectiveGrade = isFabricValid ? liveGrade : "INVALID";
  const effectiveScore = isFabricValid ? liveQualityScore : 0.0;

  const classColorMap = {
    hole: { hex: "#DC2626", bg: "rgba(220, 38, 38, 0.08)", border: "border-red-200", text: "text-red-700" },
    knot: { hex: "#4B5563", bg: "rgba(75, 85, 99, 0.08)", border: "border-gray-200", text: "text-gray-700" },
    stain: { hex: "#D97706", bg: "rgba(217, 119, 6, 0.08)", border: "border-amber-200", text: "text-amber-800" },
  };

  const originalUrl = inspection.image?.original_url
    ? `${API_BASE}${inspection.image.original_url}`
    : null;
  const annotatedUrl = inspection.image?.annotated_url
    ? `${API_BASE}${inspection.image.annotated_url}`
    : null;

  return (
    <div className="space-y-4">

      {/* Top Specimen & Control Bar */}
      <div className="panel-enterprise p-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-[#171717] tracking-wide">
                {iid}
              </span>
              <span className="text-[#DCDCDC]">/</span>
              <span className="text-xs font-mono text-[#525252]">
                {inspection.timestamp?.replace("T", " ").slice(0, 19)}
              </span>
              <span className="text-[#DCDCDC]">/</span>
              <span className="text-xs font-mono text-[#525252]">
                {imgW}×{imgH} px
              </span>
            </div>
            <h2 className="text-sm font-bold text-[#171717] tracking-tight mt-0.5">
              Optical Defect Localization Workbench
            </h2>
          </div>
        </div>

        {/* Right Action Matrix */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 px-2.5 py-1 rounded-lg bg-[#EAEAEA] border border-[#DCDCDC] font-mono text-xs">
            <span className="text-[#525252]">GRADE</span>
            <span className={`font-bold ${
              effectiveGrade === "A" ? "text-[#137333]" :
              effectiveGrade === "B" ? "text-[#333333]" :
              effectiveGrade === "C" ? "text-[#B06000]" : "text-[#C5221F]"
            }`}>
              {effectiveGrade}
            </span>
            <span className="text-[#DCDCDC]">|</span>
            <span className="text-[#171717] font-semibold">{effectiveScore.toFixed(1)}/100</span>
          </div>

          <button
            onClick={onNavigateStructural}
            className="px-3 py-1.5 rounded-lg bg-[#F5F5F5] hover:bg-[#EAEAEA] text-[#333333] border border-[#DCDCDC] text-xs font-medium flex items-center gap-1.5 transition-colors shadow-2xs cursor-pointer"
          >
            <Compass className="w-3.5 h-3.5 text-[#525252]" />
            <span>Weave Telemetry</span>
          </button>

          <button
            onClick={onNavigateQuality}
            className="px-3 py-1.5 rounded-lg bg-[#F5F5F5] hover:bg-[#EAEAEA] text-[#333333] border border-[#DCDCDC] text-xs font-medium flex items-center gap-1.5 transition-colors shadow-2xs cursor-pointer"
          >
            <Award className="w-3.5 h-3.5 text-[#137333]" />
            <span>Audit Scorecard</span>
          </button>

          <button
            onClick={onOpenReport}
            className="px-3 py-1.5 rounded-lg bg-[#171717] hover:bg-[#262626] text-[#F5F5F5] text-xs font-medium flex items-center gap-1.5 transition-colors shadow-xs cursor-pointer font-sans"
          >
            <FileDown className="w-3.5 h-3.5" />
            <span>Audit PDF</span>
          </button>
        </div>
      </div>

      {/* Non-Fabric Specimen Rejection Alert Banner */}
      {!isFabricValid && (
        <div className="p-4 rounded-xl bg-[#FCE8E6] border border-[#FAD2CF] text-[#C5221F] space-y-2 font-sans shadow-xs">
          <div className="flex items-start gap-3">
            <ShieldAlert className="w-5 h-5 flex-shrink-0 text-[#C5221F] mt-0.5" />
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm text-[#C5221F] tracking-tight uppercase">
                  Specimen Rejected — Non-Fabric Image Detected
                </span>
                <span className="text-[10px] font-mono font-semibold bg-[#C5221F] text-white px-2 py-0.5 rounded-sm">
                  SCANNING BYPASSED
                </span>
              </div>
              <p className="text-xs text-[#525252] leading-relaxed">
                The uploaded specimen was identified as <b className="text-[#171717]">invalid photo</b> rather than an authentic textile fabric photo. Automated Faster R-CNN defect proposal was bypassed to prevent false-positive defect alarms on non-fabric surfaces.
              </p>
              <p className="text-xs text-[#525252]">
                <b className="text-[#171717]">Recommendation:</b> Please upload a close-up photograph of woven fabric, knitwear, or textile material.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Phase 9 Standardized Telemetry Matrix */}
      <div className="panel-enterprise p-4 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3 font-mono text-xs">
        
        {/* 1. Material Status */}
        <div className="p-2.5 rounded-lg bg-[#EAEAEA] border border-[#DCDCDC] space-y-1">
          <span className="text-[10px] text-[#525252] uppercase block font-semibold">Material Status</span>
          <div className="flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${isFabricValid ? "bg-[#137333]" : "bg-[#C5221F]"}`}></span>
            <span className={`font-bold text-xs ${isFabricValid ? "text-[#137333]" : "text-[#C5221F]"}`}>
              {isFabricValid ? "Fabric Verified" : "Non-Fabric"}
            </span>
          </div>
        </div>

        {/* 2. Detection Status */}
        <div className="p-2.5 rounded-lg bg-[#EAEAEA] border border-[#DCDCDC] space-y-1">
          <span className="text-[10px] text-[#525252] uppercase block font-semibold">Detection Status</span>
          <div className="flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${
              !isFabricValid ? "bg-[#737373]" :
              liveCounts.total > 0 ? "bg-[#C5221F]" : "bg-[#137333]"
            }`}></span>
            <span className="font-bold text-xs text-[#171717]">
              {!isFabricValid ? "Scanning Bypassed" : liveCounts.total > 0 ? "Defects Detected" : "No Defects"}
            </span>
          </div>
        </div>

        {/* 3. Defect Count: Hole */}
        <div className="p-2.5 rounded-lg bg-[#EAEAEA] border border-[#DCDCDC] space-y-1">
          <span className="text-[10px] text-[#525252] uppercase block font-semibold">Hole Count</span>
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#DC2626]"></span>
            <span className="font-bold text-xs text-[#171717]">{liveCounts.hole}</span>
            <span className="text-[10px] text-[#737373]">defects</span>
          </div>
        </div>

        {/* 4. Defect Count: Knot */}
        <div className="p-2.5 rounded-lg bg-[#EAEAEA] border border-[#DCDCDC] space-y-1">
          <span className="text-[10px] text-[#525252] uppercase block font-semibold">Knot Count</span>
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#525252]"></span>
            <span className="font-bold text-xs text-[#171717]">{liveCounts.knot}</span>
            <span className="text-[10px] text-[#737373]">defects</span>
          </div>
        </div>

        {/* 5. Defect Count: Stain */}
        <div className="p-2.5 rounded-lg bg-[#EAEAEA] border border-[#DCDCDC] space-y-1">
          <span className="text-[10px] text-[#525252] uppercase block font-semibold">Stain Count</span>
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#B06000]"></span>
            <span className="font-bold text-xs text-[#171717]">{liveCounts.stain}</span>
            <span className="text-[10px] text-[#737373]">defects</span>
          </div>
        </div>

        {/* 6. Model Architecture & Device */}
        <div className="p-2.5 rounded-lg bg-[#EAEAEA] border border-[#DCDCDC] space-y-1">
          <span className="text-[10px] text-[#525252] uppercase block font-semibold">Model / Device</span>
          <div className="truncate text-xs font-bold text-[#171717]" title="Faster R-CNN + ResNet-50 FPN">
            Faster R-CNN / {inspection.model?.device?.toUpperCase() || "CPU"}
          </div>
        </div>

        {/* 7. Inference Time & Threshold */}
        <div className="p-2.5 rounded-lg bg-[#EAEAEA] border border-[#DCDCDC] space-y-1">
          <span className="text-[10px] text-[#525252] uppercase block font-semibold">Inference / Cutoff</span>
          <div className="text-xs font-bold text-[#171717]">
            {inspection.timing?.inference_time_ms || 0} ms | {(threshold * 100).toFixed(0)}%
          </div>
        </div>

      </div>

      {/* Industrial Sensitivity & Model Calibration Strip */}
      <div className="panel-enterprise p-4 space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-[#525252]" />
            <span className="font-semibold text-[#171717]">Detector Sensitivity Calibration</span>
            <span className="text-[10px] text-[#525252] bg-[#EAEAEA] px-2 py-0.5 rounded-md border border-[#DCDCDC] font-mono">
              FASTER R-CNN FPN
            </span>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-xs">
              <span className="text-[#525252]">Cutoff:</span>
              <span className="text-[#171717] font-bold bg-[#EAEAEA] px-2 py-0.5 rounded-md border border-[#DCDCDC] font-mono">
                {(threshold * 100).toFixed(0)}% (τ = {threshold.toFixed(2)})
              </span>
            </div>

            <button
              onClick={handleApplyThreshold}
              disabled={isSaving || !isFabricValid}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-all shadow-xs cursor-pointer ${
                !isFabricValid
                  ? "bg-[#E2E2E2] text-[#737373] cursor-not-allowed border border-[#DCDCDC]"
                  : "bg-[#171717] hover:bg-[#262626] text-[#F5F5F5]"
              }`}
            >
              {isSaving ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Save className="w-3.5 h-3.5" />
              )}
              <span>Commit & Re-generate PDF</span>
            </button>
          </div>
        </div>

        {/* Slider Track */}
        <div className="space-y-1 pt-1">
          <input
            type="range"
            min="0.05"
            max="0.95"
            step="0.01"
            value={threshold}
            disabled={!isFabricValid}
            onChange={(e) => setThreshold(parseFloat(e.target.value))}
            className="w-full h-1.5 bg-[#DCDCDC] rounded accent-[#171717] cursor-pointer"
          />
          <div className="flex justify-between text-[10.5px] text-[#737373] font-mono">
            <span>0.05 (Maximum Anomaly Recall)</span>
            <span>0.50 (Calibrated Nominal)</span>
            <span>0.95 (High Specificity)</span>
          </div>
        </div>

        {saveMessage && (
          <div className="text-[11px] font-mono text-[#137333] bg-[#E6F4EA] px-2.5 py-1 rounded-md border border-[#CEEAD6] flex items-center gap-2">
            <CheckCircle className="w-3 h-3" />
            <span>{saveMessage}</span>
          </div>
        )}
      </div>

      {/* Main Inspection Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">

        {/* Left Column (7): Optical Canvas with Reticles */}
        <div className="lg:col-span-7 space-y-2">
          <div className="panel-enterprise p-4 space-y-3">
            
            {/* Workbench View Toolbar */}
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#DCDCDC] pb-3">
              <div className="flex items-center gap-1 bg-[#EAEAEA] p-1 rounded-lg border border-[#DCDCDC]">
                <button
                  onClick={() => setActiveTab("interactive")}
                  className={`px-3 py-1 rounded-md text-xs transition-all cursor-pointer ${
                    activeTab === "interactive"
                      ? "bg-[#F5F5F5] text-[#171717] font-semibold shadow-xs"
                      : "text-[#525252] hover:text-[#171717]"
                  }`}
                >
                  AI Detection Boxes ({displayBoxes.length})
                </button>
                <button
                  onClick={() => setActiveTab("server")}
                  className={`px-3 py-1 rounded-md text-xs transition-all cursor-pointer ${
                    activeTab === "server"
                      ? "bg-[#F5F5F5] text-[#171717] font-semibold shadow-xs"
                      : "text-[#525252] hover:text-[#171717]"
                  }`}
                >
                  Annotated Output
                </button>
                <button
                  onClick={() => setActiveTab("raw")}
                  className={`px-3 py-1 rounded-md text-xs transition-all cursor-pointer ${
                    activeTab === "raw"
                      ? "bg-[#F5F5F5] text-[#171717] font-semibold shadow-xs"
                      : "text-[#525252] hover:text-[#171717]"
                  }`}
                >
                  Original Photo
                </button>
              </div>

              {/* Viewport controls */}
              <div className="flex items-center gap-2 text-xs">
                <button
                  onClick={() => setShowCrosshair(!showCrosshair)}
                  className={`px-2.5 py-1 rounded-md border text-[11px] flex items-center gap-1 transition-all cursor-pointer ${
                    showCrosshair
                      ? "bg-[#171717] text-[#F5F5F5] border-[#171717]"
                      : "bg-[#F5F5F5] text-[#525252] border-[#DCDCDC] hover:text-[#171717]"
                  }`}
                  title="Toggle Center Crosshairs"
                >
                  <Crosshair className="w-3 h-3" />
                  <span>Grid</span>
                </button>

                <button
                  onClick={() => setShowLabels(!showLabels)}
                  className={`px-2.5 py-1 rounded-md border text-[11px] flex items-center gap-1 transition-all cursor-pointer ${
                    showLabels
                      ? "bg-[#171717] text-[#F5F5F5] border-[#171717]"
                      : "bg-[#F5F5F5] text-[#525252] border-[#DCDCDC] hover:text-[#171717]"
                  }`}
                  title="Toggle Box Labels"
                >
                  <Tag className="w-3 h-3" />
                  <span>Labels</span>
                </button>
              </div>
            </div>

            {/* Specimen Viewport */}
            <div className="relative aspect-square w-full bg-[#EAEAEA] border border-[#DCDCDC] rounded-xl overflow-hidden flex items-center justify-center select-none shadow-xs">
              
              {activeTab === "interactive" ? (
                <div className="relative w-full h-full">
                  <img
                    src={originalUrl}
                    alt="Fabric specimen"
                    className="w-full h-full object-contain pointer-events-none"
                  />

                  {/* SVG Reticles and Bounding Boxes */}
                  <svg
                    viewBox={`0 0 ${imgW} ${imgH}`}
                    className="absolute inset-0 w-full h-full pointer-events-none"
                    preserveAspectRatio="xMidYMid meet"
                  >
                    {/* Optional Crosshair Graticule */}
                    {showCrosshair && (
                      <g stroke="#888888" strokeWidth="0.75" strokeDasharray="3 3" opacity="0.35">
                        <line x1="0" y1={imgH / 2} x2={imgW} y2={imgH / 2} />
                        <line x1={imgW / 2} y1="0" x2={imgW / 2} y2={imgH} />
                        <circle cx={imgW / 2} cy={imgH / 2} r="18" fill="none" />
                        <circle cx={imgW / 2} cy={imgH / 2} r="2" fill="#888888" />
                      </g>
                    )}

                    {displayBoxes.map((box, idx) => {
                      const [x1, y1, x2, y2] = box.bbox || [0, 0, 0, 0];
                      const bw = Math.max(1, x2 - x1);
                      const bh = Math.max(1, y2 - y1);
                      const cls = box.class.toLowerCase();
                      const colorInfo = classColorMap[cls] || classColorMap.hole;
                      const isHovered = hoveredBox === idx;
                      const arm = Math.min(10, Math.min(bw, bh) * 0.3);

                      return (
                        <g key={idx}>
                          {/* Box Shading */}
                          <rect
                            x={x1}
                            y={y1}
                            width={bw}
                            height={bh}
                            fill={colorInfo.bg}
                            stroke={colorInfo.hex}
                            strokeWidth={isHovered ? 2.5 : 1.5}
                            strokeDasharray={isHovered ? "4 2" : "none"}
                          />

                          {/* Optical Precision Corner Reticles */}
                          <path
                            d={`
                              M ${x1} ${y1 + arm} L ${x1} ${y1} L ${x1 + arm} ${y1}
                              M ${x2 - arm} ${y1} L ${x2} ${y1} L ${x2} ${y1 + arm}
                              M ${x1} ${y2 - arm} L ${x1} ${y2} L ${x1 + arm} ${y2}
                              M ${x2 - arm} ${y2} L ${x2} ${y2} L ${x2} ${y2 - arm}
                            `}
                            stroke="#171717"
                            strokeWidth={1.5}
                            fill="none"
                          />

                          {/* Monospaced Tag Pill */}
                          {showLabels && (
                            <g transform={`translate(${x1}, ${Math.max(0, y1 - 18)})`}>
                              <rect
                                x="0"
                                y="0"
                                width={Math.max(76, cls.length * 8 + 44)}
                                height="16"
                                rx="3"
                                fill="#F5F5F5"
                                stroke={colorInfo.hex}
                                strokeWidth="1"
                              />
                              <text
                                x="4"
                                y="12"
                                fill={colorInfo.hex}
                                fontSize="9.5"
                                fontWeight="700"
                                fontFamily="monospace"
                              >
                                {cls.toUpperCase()} {(box.confidence * 100).toFixed(0)}%
                              </text>
                            </g>
                          )}
                        </g>
                      );
                    })}
                  </svg>
                </div>
              ) : (
                <img
                  src={activeTab === "server" ? annotatedUrl : originalUrl}
                  alt="Fabric inspection view"
                  className="w-full h-full object-contain"
                />
              )}

              {/* Viewport Status Hud */}
              <div className="absolute bottom-2 left-2 px-2.5 py-1 bg-[#F5F5F5]/95 border border-[#DCDCDC] rounded-md shadow-xs font-mono text-[10px] text-[#333333] flex items-center gap-2 pointer-events-none">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                <span>RETICLE: {displayBoxes.length} DETECTED</span>
                <span className="text-[#DCDCDC]">|</span>
                <span>CUTOFF: {(threshold * 100).toFixed(0)}%</span>
              </div>
            </div>

          </div>
        </div>

        {/* Right Column (5): Defect Inventory & Anomaly Table */}
        <div className="lg:col-span-5 space-y-3">
          
          {/* Class Filter Strip */}
          <div className="panel-enterprise p-3.5 space-y-2">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-[#525252] uppercase tracking-wider font-semibold">Classification Filter</span>
              <span className="text-[#171717] font-semibold">{displayBoxes.length} active</span>
            </div>
            <div className="grid grid-cols-4 gap-1.5">
              {[
                { id: "all", label: "ALL", count: liveCounts.total },
                { id: "hole", label: "HOLE", count: liveCounts.hole },
                { id: "knot", label: "KNOT", count: liveCounts.knot },
                { id: "stain", label: "STAIN", count: liveCounts.stain },
              ].map((f) => (
                <button
                  key={f.id}
                  onClick={() => setSelectedClassFilter(f.id)}
                  className={`py-1.5 px-1 rounded-lg text-center font-mono text-[11px] transition-colors border ${
                    selectedClassFilter === f.id
                      ? "bg-[#171717] text-[#F5F5F5] font-semibold border-[#171717] shadow-xs"
                      : "bg-[#F5F5F5] text-[#333333] border-[#DCDCDC] hover:bg-[#EAEAEA] hover:text-[#171717]"
                  }`}
                >
                  <div>{f.label}</div>
                  <div className="text-[9.5px] opacity-80">({f.count})</div>
                </button>
              ))}
            </div>
          </div>

          {/* High-Density Defect Inventory */}
          <div className="panel-enterprise p-3.5 space-y-2.5">
            <div className="flex items-center justify-between text-xs font-mono border-b border-[#DCDCDC] pb-2">
              <span className="font-semibold text-[#171717] uppercase tracking-wider">Defect Registry</span>
              <span className="text-[10px] text-[#525252]">ASTM D5430 POINT TALLY</span>
            </div>

            <div className="space-y-1.5 max-h-[460px] overflow-y-auto pr-1">
              {displayBoxes.length > 0 ? (
                displayBoxes.map((d, index) => {
                  const isHovered = hoveredBox === index;
                  const cls = d.class.toLowerCase();
                  const colorInfo = classColorMap[cls] || classColorMap.hole;
                  const bbox = d.bbox || [0, 0, 0, 0];
                  const bw = Math.max(0, bbox[2] - bbox[0]);
                  const bh = Math.max(0, bbox[3] - bbox[1]);
                  const area = d.area_px || Math.round(bw * bh);
                  const areaPct = ((area / (imgW * imgH)) * 100).toFixed(2);

                  return (
                    <div
                      key={index}
                      onMouseEnter={() => setHoveredBox(index)}
                      onMouseLeave={() => setHoveredBox(null)}
                      className={`p-2.5 rounded-lg border transition-colors font-mono text-xs ${
                        isHovered
                          ? "bg-[#E2E2E2] border-[#C4C4C4] shadow-xs"
                          : "bg-[#F5F5F5] border-[#DCDCDC] hover:border-[#C4C4C4]"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-[#525252] font-bold">
                            #{String(index + 1).padStart(2, "0")}
                          </span>
                          <span className={`px-2 py-0.5 rounded border text-[10px] font-bold uppercase ${colorInfo.border} ${colorInfo.text} bg-[#F5F5F5]`}>
                            {d.class}
                          </span>
                        </div>
                        <span className="font-bold text-[#171717]">
                          {(d.confidence * 100).toFixed(1)}% conf
                        </span>
                      </div>

                      <div className="grid grid-cols-2 gap-x-2 gap-y-1 mt-2 text-[10.5px] text-[#525252] pt-2 border-t border-[#DCDCDC]">
                        <div>
                          <span className="text-[#525252]">Box: </span>
                          <span className="text-[#171717]">
                            [{bbox.map((v) => Math.round(v)).join(",")}]
                          </span>
                        </div>
                        <div>
                          <span className="text-[#525252]">Span: </span>
                          <span className="text-[#171717]">
                            {Math.round(bw)}×{Math.round(bh)} px
                          </span>
                        </div>
                        <div>
                          <span className="text-[#525252]">Area: </span>
                          <span className="text-[#171717]">
                            {area.toLocaleString()} px² ({areaPct}%)
                          </span>
                        </div>
                        <div>
                          <span className="text-[#525252]">Severity: </span>
                          <span className={`font-semibold ${
                            cls === "hole" ? "text-red-700" : cls === "knot" ? "text-gray-700" : "text-amber-700"
                          }`}>
                            {cls === "hole" ? "Major" : cls === "knot" ? "Moderate" : "Minor"}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })
              ) : !isFabricValid ? (
                <div className="p-6 text-center space-y-2 border border-red-200 bg-red-50 rounded-xl">
                  <ShieldAlert className="w-6 h-6 text-red-600 mx-auto" />
                  <div className="text-xs font-mono font-bold text-red-700">
                    ANOMALY PROPOSALS SUPPRESSED
                  </div>
                  <p className="text-[10.5px] font-mono text-gray-500">
                    Specimen failed domain authentication (classified as {fabricVal.detected_category || "Non-Fabric"}).
                  </p>
                </div>
              ) : (
                <div className="p-8 text-center space-y-1.5 border border-[#DCDCDC] rounded-xl bg-[#EAEAEA]">
                  <CheckCircle className="w-6 h-6 text-emerald-600 mx-auto opacity-80" />
                  <div className="text-xs font-mono font-bold text-[#171717]">
                    NO DEFECTS AT &ge; {(threshold * 100).toFixed(0)}% THRESHOLD
                  </div>
                  <p className="text-[10.5px] font-mono text-[#525252]">
                    Adjust the sensitivity slider above to lower the proposal cutoff.
                  </p>
                </div>
              )}
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}
