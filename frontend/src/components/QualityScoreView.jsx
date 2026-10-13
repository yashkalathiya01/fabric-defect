import React from "react";
import {
  Award,
  FileCheck,
  CheckCircle,
  AlertTriangle,
  FileDown,
  Info,
  Sliders,
  ShieldCheck,
  Percent,
  Layers,
  ShieldAlert,
  FileText,
} from "lucide-react";

export default function QualityScoreView({ inspection, onOpenReport }) {
  if (!inspection) {
    return (
      <div className="panel-enterprise p-12 text-center space-y-4">
        <AlertTriangle className="w-10 h-10 text-amber-600 mx-auto opacity-80" />
        <h3 className="text-base font-semibold text-[#171717]">No Quality Assessment Loaded</h3>
        <p className="text-xs text-[#525252]">Complete an inspection scan to generate the quality disposition certificate.</p>
      </div>
    );
  }

  const quality = inspection.quality || {};
  const grade = quality.grade || "D";
  const score = quality.quality_score || 0;
  const defectScore = quality.defect_score || 0;
  const structureScore = quality.structure_score || 0;
  const gradeDesc = quality.grade_description || "";
  const methodology = quality.methodology || {};

  const gradeStyles = {
    A: {
      statusText: "PASS • FIRST QUALITY (PREMIUM)",
      chipClass: "chip-status-pass",
      accentColor: "#137333",
      code: "RELEASED",
    },
    B: {
      statusText: "PASS • SECOND QUALITY (COMMERCIAL)",
      chipClass: "chip-status-steel",
      accentColor: "#525252",
      code: "COMMERCIAL RELEASE",
    },
    C: {
      statusText: "CONDITIONAL • THIRD QUALITY (SUBSTANDARD)",
      chipClass: "chip-status-warn",
      accentColor: "#B06000",
      code: "SECONDARY MARKET",
    },
    D: {
      statusText: "FAIL • FACTORY REJECT (MILL SCRAP)",
      chipClass: "chip-status-fail",
      accentColor: "#C5221F",
      code: "DISPOSITION: SCRAP",
    },
    INVALID: {
      statusText: "QUARANTINE • NON-CONFORMING SPECIMEN",
      chipClass: "chip-status-fail",
      accentColor: "#C5221F",
      code: "REJECTED: NON-FABRIC",
    },
  };

  const currentStatus = gradeStyles[grade] || gradeStyles.D;

  // SVG Circular progress radius
  const radius = 64;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      
      {/* Top Header */}
      <div className="panel-enterprise p-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-semibold text-[#525252]">
              AUDIT CERTIFICATE
            </span>
            <span className="text-[#A3A3A3]">/</span>
            <span className="text-xs font-mono text-[#525252]">
              ISO 9001:2015 CLAUSE 8.6 • ASTM D5430-07
            </span>
          </div>
          <h2 className="text-base font-semibold text-[#171717] tracking-tight mt-0.5">
            Fabric Inspection Disposition Certificate: {inspection.inspection_id}
          </h2>
        </div>

        <button
          onClick={onOpenReport}
          className="btn-enterprise-primary text-xs flex items-center gap-2"
        >
          <FileDown className="w-3.5 h-3.5" />
          <span>Export Official PDF Report</span>
        </button>
      </div>

      {/* Hero Certificate Block */}
      <div className="panel-enterprise p-6 space-y-5">
        
        {/* Certificate Header Stamp */}
        <div className="flex flex-wrap items-start justify-between gap-4 border-b border-[#DCDCDC] pb-4">
          <div className="space-y-1">
            <span className="text-[10px] font-mono text-[#525252] uppercase tracking-widest block font-semibold">
              TEXVISION INDUSTRIAL OPTICAL TELEMETRY
            </span>
            <div className="flex items-center gap-3">
              <span className={`chip-status ${currentStatus.chipClass} font-mono text-xs font-bold`}>
                {grade === "INVALID" ? "QUARANTINED SPECIMEN" : `GRADE ${grade}`}
              </span>
              <span className="text-xs font-mono font-semibold text-[#171717]">
                {currentStatus.statusText}
              </span>
            </div>
          </div>

          <div className="text-right font-mono text-xs text-[#525252]">
            <div>SPECIMEN LOT: <span className="text-[#171717] font-bold">{inspection.inspection_id}</span></div>
            <div>TIMESTAMP: <span className="text-[#171717]">{inspection.timestamp?.replace("T", " ").slice(0, 19)}</span></div>
          </div>
        </div>

        {/* Gauge & Metrics Row */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
          
          {/* Circular Precision Gauge (4 cols) */}
          <div className="md:col-span-4 flex flex-col items-center justify-center space-y-2">
            <div className="relative w-36 h-36 flex items-center justify-center">
              <svg className="w-full h-full transform -rotate-90">
                <circle
                  cx="72"
                  cy="72"
                  r={radius}
                  stroke="#DCDCDC"
                  strokeWidth="7"
                  fill="none"
                />
                <circle
                  cx="72"
                  cy="72"
                  r={radius}
                  stroke={currentStatus.accentColor}
                  strokeWidth="7"
                  fill="none"
                  strokeDasharray={circumference}
                  strokeDashoffset={strokeDashoffset}
                  strokeLinecap="round"
                />
              </svg>

              <div className="absolute inset-0 flex flex-col items-center justify-center text-center font-mono">
                <span className="text-2xl font-bold text-[#171717] tracking-tight">
                  {score.toFixed(1)}
                </span>
                <span className="text-[10px] text-[#525252] uppercase tracking-wider font-semibold">
                  SCALE / 100
                </span>
              </div>
            </div>

            <span className="text-xs font-mono text-[#525252]">
              Composite Quality Index
            </span>
          </div>

          {/* Detailed Disposition Text (8 cols) */}
          <div className="md:col-span-8 space-y-3 font-mono text-xs">
            <div className="bg-[#EAEAEA] p-3.5 rounded-lg border border-[#DCDCDC] space-y-1">
              <span className="text-[#525252] text-[10px] uppercase tracking-wider block font-semibold">
                Disposition Summary
              </span>
              <p className="text-[#171717] text-xs leading-relaxed">
                {gradeDesc || "Specimen evaluation completed using weighted Faster R-CNN optical defect localization and OpenCV thread orthogonality analysis."}
              </p>
            </div>

            <div className="grid grid-cols-3 gap-2.5 text-[11px]">
              <div className="bg-[#EAEAEA] p-2.5 rounded-lg border border-[#DCDCDC]">
                <span className="text-[#525252] block text-[10px]">DEFECT PENALTY</span>
                <span className="text-[#171717] font-bold text-sm">{defectScore.toFixed(1)} / 100</span>
                <span className="text-[#525252] block text-[10px]">Weight: 60%</span>
              </div>
              <div className="bg-[#EAEAEA] p-2.5 rounded-lg border border-[#DCDCDC]">
                <span className="text-[#525252] block text-[10px]">STRUCTURAL INDEX</span>
                <span className="text-[#171717] font-bold text-sm">{structureScore.toFixed(1)} / 100</span>
                <span className="text-[#525252] block text-[10px]">Weight: 40%</span>
              </div>
              <div className="bg-[#EAEAEA] p-2.5 rounded-lg border border-[#DCDCDC]">
                <span className="text-[#525252] block text-[10px]">DISPOSITION</span>
                <span className="text-[#171717] font-bold text-sm truncate block">{currentStatus.code}</span>
                <span className="text-[#525252] block text-[10px]">Verified</span>
              </div>
            </div>
          </div>

        </div>

      </div>

      {/* Component Breakdown Tables */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        
        {/* Surface Defect Breakdown */}
        <div className="panel-enterprise p-4 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono border-b border-[#DCDCDC] pb-2.5">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-3.5 h-3.5 text-red-600" />
              <span className="font-semibold text-[#171717]">SURFACE DEFECT DEDUCTIONS</span>
            </div>
            <span className="text-[#525252]">60% WEIGHT</span>
          </div>

          <div className="space-y-2 font-mono text-xs">
            <div className="flex justify-between py-1 border-b border-[#DCDCDC]">
              <span className="text-[#525252]">Total Defects Detected:</span>
              <span className="font-bold text-[#171717]">{inspection.defects?.total || 0}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#DCDCDC]">
              <span className="text-[#525252]">Defect Density (per MP):</span>
              <span className="font-bold text-[#171717]">{inspection.defect_analysis?.defect_density_per_megapixel || 0}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-[#525252]">Defect Surface Coverage:</span>
              <span className="font-bold text-[#171717]">{inspection.defect_analysis?.defect_area_percentage?.toFixed(2) || 0}%</span>
            </div>
          </div>
        </div>

        {/* Structural Breakdown */}
        <div className="panel-enterprise p-4 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono border-b border-[#DCDCDC] pb-2.5">
            <div className="flex items-center gap-2">
              <Sliders className="w-3.5 h-3.5 text-stone-600" />
              <span className="font-semibold text-[#171717]">STRUCTURAL WEAVE UNIFORMITY</span>
            </div>
            <span className="text-[#525252]">40% WEIGHT</span>
          </div>

          <div className="space-y-2 font-mono text-xs">
            <div className="flex justify-between py-1 border-b border-[#DCDCDC]">
              <span className="text-[#525252]">Orthogonal Skew (Δθ):</span>
              <span className="font-bold text-[#171717]">
                {inspection.structural_analysis?.alignment_deviation !== undefined && inspection.structural_analysis?.alignment_deviation !== null
                  ? `${inspection.structural_analysis.alignment_deviation.toFixed(2)}°`
                  : "N/A"}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#DCDCDC]">
              <span className="text-[#525252]">Warp / Weft Vectors:</span>
              <span className="font-bold text-[#171717]">
                {inspection.structural_analysis?.warp_angle
                  ? `${inspection.structural_analysis.warp_angle.toFixed(1)}° / ${inspection.structural_analysis.weft_angle.toFixed(1)}°`
                  : "Inconclusive"}
              </span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-[#525252]">Orientation Confidence:</span>
              <span className="font-bold text-[#171717]">
                {((inspection.structural_analysis?.orientation_confidence || 0) * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>

      </div>

      {/* Engineering Heuristic & ISO Compliance Footnote */}
      <div className="panel-enterprise p-4 space-y-2 font-mono text-xs">
        <div className="flex items-center gap-1.5 text-[#171717] font-semibold">
          <Info className="w-3.5 h-3.5 text-[#525252]" />
          <span>SCORING PROTOCOL SPECIFICATION</span>
        </div>
        <div className="bg-[#EAEAEA] p-2.5 rounded-lg border border-[#DCDCDC] text-[11px] text-[#171717]">
          {methodology.formula || "quality_score = 0.60 * defect_score + 0.40 * structure_score"}
        </div>
        <p className="text-[11px] text-[#525252] leading-relaxed pt-0.5">
          <b>Grading Thresholds:</b> Grade A (90–100, Premium), Grade B (75–89, Standard Commercial), Grade C (60–74, Substandard), Grade D (&lt;60, Reject).
          Formal testing in compliance with ASTM D5430 (Standard Test Methods for Visually Inspecting and Grading Fabrics) and ISO 8498.
        </p>
      </div>

    </div>
  );
}
