import React, { useState } from "react";
import Sidebar from "./components/Sidebar";
import DashboardView from "./components/DashboardView";
import NewInspectionView from "./components/NewInspectionView";
import DetectionResultView from "./components/DetectionResultView";
import StructuralAnalysisView from "./components/StructuralAnalysisView";
import QualityScoreView from "./components/QualityScoreView";
import InspectionHistoryView from "./components/InspectionHistoryView";
import ReportModal from "./components/ReportModal";

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [currentInspection, setCurrentInspection] = useState(null);
  const [initialSample, setInitialSample] = useState(null);
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Handle when an inspection finishes
  const handleInspectionComplete = (inspectionData) => {
    setCurrentInspection(inspectionData);
    setActiveTab("results");
  };

  // Handle 1-click sample selection from dashboard
  const handleSelectSample = (sampleFilename) => {
    setInitialSample(sampleFilename);
    setActiveTab("inspect");
  };

  // Handle loading a historical inspection record
  const handleLoadHistoryDetail = async (inspectionId) => {
    try {
      const res = await fetch(`http://localhost:8000/api/inspections/${inspectionId}`);
      if (res.ok) {
        const data = await res.json();
        setCurrentInspection(data);
        setActiveTab("results");
      }
    } catch (err) {
      console.error("Failed to load historical inspection detail:", err);
    }
  };

  // Navigation tab display metadata
  const tabTitles = {
    dashboard: "Operations Terminal & KPI Telemetry",
    inspect: "Specimen Ingestion & Calibration Studio",
    results: "Computer Vision Defect Workbench",
    structure: "Edge, Threshold & Luminance Laboratory",
    quality: "Quality Certification & ASTM Compliance",
    history: "Lot Archive & Audit Registry",
  };

  return (
    <div className="min-h-screen text-[#171717] flex font-sans bg-[#F5F5F5]">
      
      {/* Left Sliding Navigation Slidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        hasInspection={!!currentInspection}
        currentLotId={currentInspection?.inspection_id}
        isMobileOpen={isMobileOpen}
        setIsMobileOpen={setIsMobileOpen}
        isCollapsed={isCollapsed}
        setIsCollapsed={setIsCollapsed}
      />

      {/* Right Main Content Area */}
      <div className="flex-1 min-w-0 flex flex-col min-h-screen transition-all duration-300">
        
        {/* Top Header Breadcrumb & Telemetry Strip */}
        <header className="sticky top-0 z-20 w-full border-b border-[#DCDCDC] bg-[#F5F5F5]/95 backdrop-blur-xs px-4 sm:px-6 py-3 flex items-center justify-between shadow-2xs">
          <div className="flex items-center gap-3">
            {/* Breadcrumb trail */}
            <div className="flex items-center gap-2 text-xs font-mono">
              <span className="text-[#737373] uppercase font-semibold">Workspace</span>
              <span className="text-[#DCDCDC]">/</span>
              <span className="text-[#171717] font-bold uppercase tracking-wide">{activeTab}</span>
              <span className="text-[#DCDCDC]">•</span>
              <span className="text-[#525252] font-sans font-medium">{tabTitles[activeTab] || ""}</span>
            </div>
          </div>

          {/* Right side telemetry & quick indicators */}
          <div className="flex items-center gap-3 text-xs font-mono">
            {currentInspection && (
              <div className="hidden sm:flex items-center gap-2 bg-[#EAEAEA] px-2.5 py-1 rounded-lg border border-[#DCDCDC]">
                <span className="text-[#525252]">LOT:</span>
                <span className="text-[#171717] font-bold">{currentInspection.inspection_id}</span>
                <span className="text-[#DCDCDC]">|</span>
                <span className="chip-status chip-status-pass text-[10px]">
                  GRADE {currentInspection.quality?.grade || "D"}
                </span>
              </div>
            )}
            <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#E6F4EA] border border-[#CEEAD6] text-[11px] font-mono text-[#137333] font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-[#137333]"></span>
              <span>SYSTEM READY</span>
            </div>
          </div>
        </header>

        {/* Main Workspace Viewport */}
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
          
          {/* 1. Dashboard View */}
          {activeTab === "dashboard" && (
            <DashboardView
              onSelectSample={handleSelectSample}
              onInspectNew={() => setActiveTab("inspect")}
              onViewHistoryDetail={handleLoadHistoryDetail}
            />
          )}

          {/* 2. New Inspection Studio */}
          {activeTab === "inspect" && (
            <NewInspectionView
              onInspectionComplete={handleInspectionComplete}
              initialSampleFilename={initialSample}
              onClearInitialSample={() => setInitialSample(null)}
            />
          )}

          {/* 3. Defect Explorer */}
          {activeTab === "results" && (
            <DetectionResultView
              inspection={currentInspection}
              onNavigateStructural={() => setActiveTab("structure")}
              onNavigateQuality={() => setActiveTab("quality")}
              onOpenReport={() => setReportModalOpen(true)}
              onInspectionUpdated={(updated) => setCurrentInspection(updated)}
            />
          )}

          {/* 4. OpenCV Structural Laboratory */}
          {activeTab === "structure" && (
            <StructuralAnalysisView inspection={currentInspection} />
          )}

          {/* 5. Quality Scorecard & Grading */}
          {activeTab === "quality" && (
            <QualityScoreView
              inspection={currentInspection}
              onOpenReport={() => setReportModalOpen(true)}
            />
          )}

          {/* 6. Archives & Reports */}
          {activeTab === "history" && (
            <InspectionHistoryView
              onSelectInspection={handleLoadHistoryDetail}
              onHistoryCleared={() => setCurrentInspection(null)}
              onInspectionDeleted={(deletedId) => {
                if (currentInspection?.inspection_id === deletedId) {
                  setCurrentInspection(null);
                }
              }}
            />
          )}

        </main>

        {/* Industrial Audit Footer */}
        <footer className="border-t border-[#DCDCDC] bg-[#F5F5F5] py-3.5 text-xs text-[#525252] font-mono px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="font-bold text-[#171717]">TEXVISION QA</span>
              <span className="text-[#DCDCDC]">•</span>
              <span>Automated Textile Optical Defect & Structure Inspection System</span>
            </div>
            <div className="flex items-center gap-3 text-[11px]">
              <span>ISO 9001 / ASTM D5430 QA PIPELINE</span>
              <span className="text-[#DCDCDC]">•</span>
              <span className="text-[#171717] font-semibold">ENTERPRISE v1.0</span>
            </div>
          </div>
        </footer>

        {/* In-App PDF Report Modal */}
        <ReportModal
          inspectionId={currentInspection?.inspection_id}
          isOpen={reportModalOpen}
          onClose={() => setReportModalOpen(false)}
        />

      </div>

    </div>
  );
}
