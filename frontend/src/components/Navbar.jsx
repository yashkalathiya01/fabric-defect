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
} from "lucide-react";

import { fetchHealth } from "../api";

export default function Navbar({ activeTab, setActiveTab, hasInspection }) {
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
    { id: "dashboard", label: "Dashboard", icon: Activity },
    { id: "inspect", label: "New Inspection", icon: ScanLine },
    { id: "results", label: "Defect Workbench", icon: Layers, disabled: !hasInspection },
    { id: "structure", label: "Weave Laboratory", icon: Compass, disabled: !hasInspection },
    { id: "quality", label: "Quality Certificate", icon: FileCheck, disabled: !hasInspection },
    { id: "history", label: "Audit Registry", icon: History },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-[#E8E3D9] bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
        
        {/* Enterprise Brand Logo */}
        <div 
          onClick={() => setActiveTab("dashboard")}
          className="flex items-center gap-3 cursor-pointer select-none"
        >
          <div className="w-8 h-8 rounded-lg bg-[#1C1917] flex items-center justify-center text-white shadow-xs">
            <ScanLine className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm tracking-tight text-[#1C1917]">
                TEX<span className="text-stone-600">VISION</span><span className="text-stone-400 font-normal ml-1">QA</span>
              </span>
              <span className="px-1.5 py-0.2 text-[9px] font-mono font-semibold tracking-wider uppercase rounded bg-[#F5F1E8] text-[#57534E] border border-[#E8E3D9]">
                PROD v1.0
              </span>
            </div>
            <p className="text-[10px] text-[#78716C] hidden sm:block">
              Industrial Optical Quality Control
            </p>
          </div>
        </div>

        {/* Segmented Navigation Bar */}
        <nav className="hidden md:flex items-center gap-1 bg-[#F5F1E8] p-1 rounded-xl border border-[#E8E3D9]">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => !item.disabled && setActiveTab(item.id)}
                disabled={item.disabled}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? "bg-white text-[#1C1917] shadow-xs font-semibold"
                    : item.disabled
                    ? "text-stone-400 cursor-not-allowed opacity-50"
                    : "text-[#78716C] hover:text-[#1C1917] hover:bg-white/60"
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? "text-[#1C1917]" : "text-[#78716C]"}`} />
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* Right Status Indicators & Action */}
        <div className="flex items-center gap-2.5">
          
          {/* Server / Model Telemetry Chip */}
          <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded-lg bg-[#F5F1E8] border border-[#E8E3D9] text-xs font-mono">
            <span
              className={`w-2 h-2 rounded-full ${
                online ? "bg-emerald-600" : "bg-red-600"
              }`}
            ></span>
            <span className="text-[#78716C] text-[11px]">
              {online ? `PORT 8000 OK` : "OFFLINE"}
            </span>
          </div>

          {/* New Inspection Action Button */}
          <button
            onClick={() => setActiveTab("inspect")}
            className="btn-enterprise-primary text-xs flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Inspect New Lot</span>
          </button>

        </div>

      </div>

      {/* Mobile Navigation Drawer */}
      <div className="flex md:hidden overflow-x-auto px-4 py-2 gap-1 border-t border-[#E8E3D9] bg-white">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => !item.disabled && setActiveTab(item.id)}
              disabled={item.disabled}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs whitespace-nowrap transition-colors ${
                isActive
                  ? "bg-[#1C1917] text-white"
                  : item.disabled
                  ? "text-stone-400 opacity-50"
                  : "text-[#78716C] hover:text-[#1C1917]"
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? "text-white" : ""}`} />
              {item.label}
            </button>
          );
        })}
      </div>
    </header>
  );
}
