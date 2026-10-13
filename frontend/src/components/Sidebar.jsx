import React, { useState, useEffect } from "react";
import {
  Layers,
  Activity,
  History,
  Compass,
  FileCheck,
  Plus,
  ScanLine,
  Server,
  X,
  ChevronRight,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";

import { fetchHealth } from "../api";

export default function Sidebar({
  activeTab,
  setActiveTab,
  hasInspection,
  currentLotId,
  isMobileOpen,
  setIsMobileOpen,
  isCollapsed = false,
  setIsCollapsed,
}) {
  const [health, setHealth] = useState(null);
  const [online, setOnline] = useState(false);

  useEffect(() => {
    const checkHealth = async () => {
      const data = await fetchHealth();
      if (data) {
        setHealth(data);
        setOnline(true);
      } else {
        setOnline(false);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 8000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    {
      id: "dashboard",
      label: "Operations Terminal",
      icon: Activity,
    },
    {
      id: "inspect",
      label: "New Inspection",
      icon: ScanLine,
    },
    {
      id: "results",
      label: "Defect Workbench",
      icon: Layers,
      disabled: !hasInspection,
    },
    {
      id: "structure",
      label: "Weave Laboratory",
      icon: Compass,
      disabled: !hasInspection,
    },
    {
      id: "quality",
      label: "Quality Certificate",
      icon: FileCheck,
      disabled: !hasInspection,
    },
    {
      id: "history",
      label: "Audit Registry",
      icon: History,
    },
  ];

  const handleNavClick = (id, disabled) => {
    if (disabled) return;
    setActiveTab(id);
    if (setIsMobileOpen) setIsMobileOpen(false);
  };

  // Render the inner content of the slidebar
  const renderSlidebar = (collapsedMode) => (
    <div className="h-full flex flex-col justify-between bg-[#F5F5F5] border-r border-[#DCDCDC] select-none shadow-2xs transition-all duration-300">
      
      {/* Top Section */}
      <div className={`space-y-3.5 ${collapsedMode ? "p-2.5" : "p-4"}`}>
        
        {/* Brand Header */}
        {collapsedMode ? (
          <div className="flex flex-col items-center gap-2 pb-3 border-b border-[#DCDCDC]">
            <div 
              onClick={() => handleNavClick("dashboard", false)}
              className="w-9 h-9 rounded-lg bg-[#171717] flex items-center justify-center text-[#F5F5F5] shadow-xs cursor-pointer hover:bg-[#262626] transition-colors"
              title="TexVision QA — Operations Terminal"
            >
              <ScanLine className="w-4 h-4" />
            </div>
            {setIsCollapsed && (
              <button
                onClick={() => setIsCollapsed(false)}
                className="p-1 rounded-md text-[#525252] hover:text-[#171717] hover:bg-[#EAEAEA] transition-colors cursor-pointer"
                title="Expand slidebar"
              >
                <PanelLeftOpen className="w-4 h-4" />
              </button>
            )}
          </div>
        ) : (
          <div className="flex items-center justify-between pb-3 border-b border-[#DCDCDC]">
            <div 
              onClick={() => handleNavClick("dashboard", false)}
              className="flex items-center gap-2.5 cursor-pointer group"
            >
              <div className="w-8 h-8 rounded-lg bg-[#171717] flex items-center justify-center text-[#F5F5F5] shadow-xs flex-shrink-0 group-hover:bg-[#262626] transition-colors">
                <ScanLine className="w-4 h-4" />
              </div>
              <div className="truncate">
                <div className="flex items-center gap-1.5">
                  <span className="font-bold text-sm tracking-tight text-[#171717] font-sans">
                    TexVision <span className="text-[#525252] font-normal">QA</span>
                  </span>
                  <span className="px-1.5 py-0.5 text-[8.5px] font-mono font-bold uppercase rounded-md bg-[#EAEAEA] text-[#333333] border border-[#DCDCDC]">
                    v1.0
                  </span>
                </div>
                <p className="text-[10px] text-[#525252] font-sans truncate">
                  Automated Textile Inspection
                </p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              {/* Desktop Slidebar Collapse Button */}
              {setIsCollapsed && (
                <button
                  onClick={() => setIsCollapsed(true)}
                  className="hidden md:flex p-1.5 rounded-lg text-[#525252] hover:text-[#171717] hover:bg-[#EAEAEA] transition-colors cursor-pointer"
                  title="Collapse slidebar (mini rail mode)"
                >
                  <PanelLeftClose className="w-4 h-4" />
                </button>
              )}

              {/* Mobile Close Button */}
              {setIsMobileOpen && (
                <button
                  onClick={() => setIsMobileOpen(false)}
                  className="md:hidden p-1.5 text-[#525252] hover:text-[#171717] rounded-lg hover:bg-[#EAEAEA] cursor-pointer"
                  title="Close slidebar"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        )}

        {/* Primary Action Button: Inspect New Lot */}
        <div>
          {collapsedMode ? (
            <button
              onClick={() => handleNavClick("inspect", false)}
              className="w-10 h-10 mx-auto rounded-lg bg-[#171717] hover:bg-[#262626] text-[#F5F5F5] flex items-center justify-center transition-all shadow-xs cursor-pointer group"
              title="Inspect New Lot"
            >
              <Plus className="w-4 h-4 stroke-[2.5] transition-transform group-hover:scale-110" />
            </button>
          ) : (
            <button
              onClick={() => handleNavClick("inspect", false)}
              className="w-full py-2.5 px-3 rounded-lg bg-[#171717] hover:bg-[#262626] text-[#F5F5F5] font-medium text-xs flex items-center justify-center gap-2 transition-all shadow-xs font-sans cursor-pointer group"
            >
              <Plus className="w-3.5 h-3.5 stroke-[2.5] transition-transform group-hover:scale-110" />
              <span>Inspect New Lot</span>
            </button>
          )}
        </div>

        {/* Active Lot Quick Glance */}
        {hasInspection && currentLotId && (
          collapsedMode ? (
            <div 
              onClick={() => handleNavClick("results", false)}
              className="w-10 h-10 mx-auto rounded-lg bg-[#EAEAEA] border border-[#DCDCDC] hover:border-[#171717] flex items-center justify-center relative cursor-pointer transition-colors shadow-2xs"
              title={`Active Specimen: ${currentLotId} (Click to view)`}
            >
              <Layers className="w-4 h-4 text-[#171717]" />
              <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-[#137333] ring-1 ring-[#F5F5F5]"></span>
            </div>
          ) : (
            <div 
              onClick={() => handleNavClick("results", false)}
              className="p-2.5 rounded-xl bg-[#EAEAEA] border border-[#DCDCDC] hover:border-[#C4C4C4] cursor-pointer transition-colors shadow-2xs"
            >
              <div className="flex items-center justify-between text-[10.5px] font-mono text-[#525252] mb-1">
                <span className="uppercase tracking-wider font-semibold">Active Specimen</span>
                <span className="w-2 h-2 rounded-full bg-[#137333] animate-pulse"></span>
              </div>
              <div className="text-xs font-mono font-bold text-[#171717] truncate">
                {currentLotId}
              </div>
              <div className="flex items-center justify-between text-[10.5px] text-[#525252] font-sans mt-1.5 pt-1.5 border-t border-[#DCDCDC]">
                <span>View workbench</span>
                <ChevronRight className="w-3.5 h-3.5 text-[#737373]" />
              </div>
            </div>
          )
        )}

        {/* Vertical Navigation Items with Scrollable Slider */}
        <div className="space-y-1">
          <nav className="space-y-1 text-xs max-h-[calc(100vh-320px)] overflow-y-auto slidebar-scrollbar pr-0.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;

              if (collapsedMode) {
                return (
                  <button
                    key={item.id}
                    onClick={() => handleNavClick(item.id, item.disabled)}
                    disabled={item.disabled}
                    title={item.label}
                    className={`w-10 h-10 mx-auto flex items-center justify-center rounded-lg transition-all cursor-pointer relative group ${
                      isActive
                        ? "bg-[#E2E2E2] text-[#171717] font-semibold border-l-3 border-[#171717] shadow-2xs"
                        : item.disabled
                        ? "text-[#737373] cursor-not-allowed opacity-40"
                        : "text-[#333333] hover:text-[#171717] hover:bg-[#EAEAEA]"
                    }`}
                  >
                    <Icon className={`w-4 h-4 flex-shrink-0 transition-transform group-hover:scale-110 ${isActive ? "text-[#171717]" : "text-[#525252]"}`} />
                  </button>
                );
              }

              return (
                <button
                  key={item.id}
                  onClick={() => handleNavClick(item.id, item.disabled)}
                  disabled={item.disabled}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-all cursor-pointer group ${
                    isActive
                      ? "bg-[#E2E2E2] text-[#171717] font-semibold border-l-3 border-[#171717] shadow-2xs"
                      : item.disabled
                      ? "text-[#737373] cursor-not-allowed opacity-50"
                      : "text-[#333333] hover:text-[#171717] hover:bg-[#EAEAEA]"
                  }`}
                >
                  <Icon className={`w-4 h-4 flex-shrink-0 transition-transform group-hover:scale-105 ${isActive ? "text-[#171717]" : "text-[#525252]"}`} />
                  <span className="truncate flex-1 font-medium">{item.label}</span>
                  {isActive && (
                    <div className="w-1.5 h-1.5 rounded-full bg-[#171717]"></div>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

      </div>

      {/* Bottom Telemetry & Status Section */}
      <div className={`border-t border-[#DCDCDC] ${collapsedMode ? "p-2.5 flex flex-col items-center gap-2" : "p-4 space-y-2 text-[10.5px]"}`}>
        {collapsedMode ? (
          <div 
            className="w-9 h-9 rounded-lg bg-[#EAEAEA] border border-[#DCDCDC] flex items-center justify-center relative cursor-pointer hover:border-[#171717] transition-colors"
            title={online ? "FastAPI Server :8000 ONLINE (Faster R-CNN active)" : "Backend Server OFFLINE"}
          >
            <Server className="w-4 h-4 text-[#333333]" />
            <span className={`absolute top-1 right-1 w-2 h-2 rounded-full ring-1 ring-[#F5F5F5] ${online ? "bg-[#137333]" : "bg-[#C5221F]"}`}></span>
          </div>
        ) : (
          <>
            {/* Server status card */}
            <div className="flex items-center justify-between p-2.5 rounded-xl bg-[#EAEAEA] border border-[#DCDCDC]">
              <div className="flex items-center gap-2">
                <span
                  className={`w-2 h-2 rounded-full ${
                    online ? "bg-[#137333]" : "bg-[#C5221F]"
                  }`}
                ></span>
                <span className="text-[#525252] font-mono">SERVER :8000</span>
              </div>
              <span className={online ? "text-[#137333] font-bold font-mono" : "text-[#C5221F] font-bold font-mono"}>
                {online ? "ONLINE" : "OFFLINE"}
              </span>
            </div>

            {/* Inference engine info */}
            <div className="px-1 text-[10px] text-[#525252] space-y-1 font-mono">
              <div className="flex justify-between">
                <span>MODEL:</span>
                <span className="text-[#171717] font-semibold">FASTER R-CNN</span>
              </div>
              <div className="flex justify-between">
                <span>DEVICE:</span>
                <span className="text-[#171717]">CPU (CALIBRATED)</span>
              </div>
              <div className="flex justify-between">
                <span>PROTOCOL:</span>
                <span className="text-[#171717]">ASTM D5430-07</span>
              </div>
            </div>
          </>
        )}
      </div>

    </div>
  );

  return (
    <>
      {/* Desktop Sticky Left Slidebar */}
      <aside
        className={`hidden md:block h-screen sticky top-0 flex-shrink-0 z-30 transition-[width] duration-300 ease-in-out ${
          isCollapsed ? "w-[72px]" : "w-64"
        }`}
      >
        {renderSlidebar(isCollapsed)}
      </aside>

      {/* Mobile Slide-out Drawer */}
      <div
        className={`md:hidden fixed inset-0 z-50 transition-opacity duration-300 ${
          isMobileOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        }`}
      >
        {/* Backdrop */}
        <div
          className="fixed inset-0 bg-stone-900/60 backdrop-blur-xs transition-opacity duration-300"
          onClick={() => setIsMobileOpen(false)}
        />
        {/* Sliding Panel */}
        <div
          className={`relative w-72 max-w-[85vw] h-full z-10 transform transition-transform duration-300 ease-in-out ${
            isMobileOpen ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          {renderSlidebar(false)}
        </div>
      </div>
    </>
  );
}
