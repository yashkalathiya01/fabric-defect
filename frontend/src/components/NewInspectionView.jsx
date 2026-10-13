import React, { useState, useRef } from "react";
import {
  Upload,
  FileImage,
  Sliders,
  ScanLine,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  RefreshCw,
  Cpu,
  Layers,
  Check,
  HardDrive,
} from "lucide-react";

import { API_BASE, inspectFabric } from "../api";

export default function NewInspectionView({
  onInspectionComplete,
  initialSampleFilename,
  onClearInitialSample,
}) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(
    initialSampleFilename
      ? `${API_BASE}/static/samples/${initialSampleFilename}`
      : null
  );
  const [isSample, setIsSample] = useState(!!initialSampleFilename);
  const [sampleFilename, setSampleFilename] = useState(initialSampleFilename || "");
  const [confThreshold, setConfThreshold] = useState(0.5);
  const [isScanning, setIsScanning] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [scanStep, setScanStep] = useState(0); // 0: idle, 1: domain check, 2: faster r-cnn, 3: opencv structure
  const fileInputRef = useRef(null);

  React.useEffect(() => {
    if (initialSampleFilename) {
      setPreviewUrl(`${API_BASE}/static/samples/${initialSampleFilename}`);
      setIsSample(true);
      setSampleFilename(initialSampleFilename);
      setSelectedFile(null);
      if (onClearInitialSample) onClearInitialSample();
    }
  }, [initialSampleFilename]);

  const handleFileDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const processFile = (file) => {
    setErrorMsg("");
    setIsSample(false);
    setSampleFilename("");
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const triggerInspect = async () => {
    if (!selectedFile && !isSample) {
      setErrorMsg("Please upload a textile specimen image or select a benchmark sample.");
      return;
    }

    setIsScanning(true);
    setErrorMsg("");
    setScanStep(1);

    // Simulated progress steps for visual feedback during server inference
    const timer1 = setTimeout(() => setScanStep(2), 600);
    const timer2 = setTimeout(() => setScanStep(3), 1400);

    try {
      const formData = new FormData();
      formData.append("confidence_threshold", confThreshold.toString());

      if (isSample) {
        const sampleRes = await fetch(previewUrl);
        const blob = await sampleRes.blob();
        formData.append("file", blob, sampleFilename || "sample.jpg");
      } else {
        formData.append("file", selectedFile);
      }

      const inspectionResult = await inspectFabric(formData);
      onInspectionComplete(inspectionResult);
    } catch (err) {
      console.error(err);
      setErrorMsg(err.message || "An unexpected error occurred during the inspection run.");
    } finally {
      clearTimeout(timer1);
      clearTimeout(timer2);
      setIsScanning(false);
      setScanStep(0);
    }
  };

  const quickSamples = [
    { label: "Hole", file: "delik-304-_jpg.rf.e01e6401271d59f7e40dc26de0fd6ece.jpg" },
    { label: "Knot", file: "dokuma-430-_jpg.rf.8f997ccd78601a61ebeb5ae55f2d2ed5.jpg" },
    { label: "Stain", file: "stain_101_jpg.rf.6ab6f399faf46315cf1c0d4348511afc.jpg" },
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-4">
      
      {/* Studio Header */}
      <div className="panel-enterprise p-5 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-[#525252] uppercase tracking-wider">
              SPECIMEN INGESTION & CALIBRATION
            </span>
            <span className="text-[#DCDCDC]">•</span>
            <span className="text-xs text-[#737373]">FASTER R-CNN + OPENCV FILTERS</span>
          </div>
          <h2 className="text-lg font-bold text-[#171717] tracking-tight mt-1">
            Initiate Automated Lot Inspection Run
          </h2>
          <p className="text-xs text-[#525252] mt-0.5">
            Ingest fabric photography for automated neural defect proposal, surface texture analysis, and quality grading.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isScanning}
            className="px-3.5 py-1.5 rounded-lg bg-[#F5F5F5] hover:bg-[#EAEAEA] text-[#171717] text-xs font-medium border border-[#DCDCDC] transition-colors shadow-2xs cursor-pointer"
          >
            Browse Disk...
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-3.5 rounded-xl bg-[#FCE8E6] border border-[#FAD2CF] text-[#C5221F] text-xs flex items-center gap-3 font-medium">
          <AlertCircle className="w-4 h-4 flex-shrink-0 text-[#C5221F]" />
          <span>ERROR: {errorMsg}</span>
        </div>
      )}

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        
        {/* Left 7 Cols: Specimen Viewport & Dropzone */}
        <div className="lg:col-span-7 space-y-4">
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleFileDrop}
            className={`panel-enterprise relative p-4 flex flex-col items-center justify-center min-h-[380px] transition-all ${
              previewUrl ? "border-[#DCDCDC] bg-[#EAEAEA]" : "border-dashed border-2 border-[#C4C4C4] bg-[#EAEAEA] hover:border-[#171717] hover:bg-[#F5F5F5]"
            }`}
          >
            {previewUrl ? (
              <div className="w-full h-full flex flex-col items-center justify-center space-y-3">
                <div className="relative max-h-[320px] rounded-lg overflow-hidden border border-[#DCDCDC] bg-[#F5F5F5] shadow-xs">
                  <img
                    src={previewUrl}
                    alt="Fabric preview"
                    className="w-full h-full object-contain max-h-[320px]"
                  />

                  {/* Processing Overlay with Telemetry Checklist */}
                  {isScanning && (
                    <div className="absolute inset-0 bg-[#F5F5F5]/95 flex flex-col items-center justify-center p-6 space-y-4 z-20">
                      <RefreshCw className="w-8 h-8 text-[#171717] animate-spin" />
                      
                      <div className="w-full max-w-xs space-y-2 font-mono text-xs">
                        <div className="text-center font-bold text-[#171717] mb-2 font-sans">
                          Executing Analysis Pipeline...
                        </div>
                        
                        <div className={`flex items-center gap-2 text-[11px] ${scanStep >= 1 ? "text-[#137333] font-semibold" : "text-[#737373]"}`}>
                          {scanStep > 1 ? <CheckCircle2 className="w-3.5 h-3.5" /> : <RefreshCw className={`w-3.5 h-3.5 ${scanStep === 1 ? "animate-spin" : ""}`} />}
                          <span>1. ResNet-50 FPN Defect Localization</span>
                        </div>

                        <div className={`flex items-center gap-2 text-[11px] ${scanStep >= 2 ? "text-[#137333] font-semibold" : "text-[#737373]"}`}>
                          {scanStep > 2 ? <CheckCircle2 className="w-3.5 h-3.5" /> : <RefreshCw className={`w-3.5 h-3.5 ${scanStep === 2 ? "animate-spin" : ""}`} />}
                          <span>2. OpenCV Structural Weave Geometry</span>
                        </div>

                        <div className={`flex items-center gap-2 text-[11px] ${scanStep >= 3 ? "text-[#137333] font-semibold" : "text-[#737373]"}`}>
                          {scanStep > 3 ? <CheckCircle2 className="w-3.5 h-3.5" /> : <RefreshCw className={`w-3.5 h-3.5 ${scanStep === 3 ? "animate-spin" : ""}`} />}
                          <span>3. ASTM D5430 Defect Scorecard & PDF</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between w-full px-2">
                  <span className="text-xs text-[#525252] truncate max-w-[280px]">
                    {selectedFile ? selectedFile.name : sampleFilename}
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      setPreviewUrl(null);
                      setSelectedFile(null);
                      setIsSample(false);
                      setSampleFilename(null);
                      if (onClearInitialSample) onClearInitialSample();
                    }}
                    className="text-xs text-[#C5221F] hover:underline font-medium cursor-pointer"
                  >
                    Clear Specimen
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-center space-y-3 p-6">
                <div className="w-12 h-12 rounded-xl bg-[#F5F5F5] border border-[#DCDCDC] text-[#171717] flex items-center justify-center mx-auto shadow-xs">
                  <Upload className="w-6 h-6" />
                </div>
                <div className="space-y-1">
                  <h4 className="text-sm font-bold text-[#171717]">
                    Drop Specimen Macro Photo Here
                  </h4>
                  <p className="text-xs text-[#525252]">
                    Supported: JPG, PNG, WEBP • Max: 50MB • Min: 256×256px
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="px-4 py-2 rounded-lg bg-[#171717] hover:bg-[#262626] text-[#F5F5F5] text-xs font-medium transition-all shadow-xs cursor-pointer"
                >
                  Select Specimen File
                </button>
              </div>
            )}

            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleFileChange}
            />
          </div>

          {/* Quick-select benchmark tabs */}
          <div className="panel-enterprise p-4 space-y-2.5">
            <span className="text-[11px] font-bold text-[#525252] uppercase tracking-wider block">
              Pre-Calibrated Benchmark Library:
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {quickSamples.map((s, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setPreviewUrl(`${API_BASE}/static/samples/${s.file}`);
                    setIsSample(true);
                    setSampleFilename(s.file);
                    setSelectedFile(null);
                    setErrorMsg("");
                  }}
                  disabled={isScanning}
                  className={`p-2.5 rounded-lg border text-center text-xs transition-all cursor-pointer ${
                    sampleFilename === s.file
                      ? "border-[#171717] bg-[#EAEAEA] text-[#171717] font-bold shadow-2xs"
                      : "border-[#DCDCDC] bg-[#F5F5F5] text-[#525252] hover:text-[#171717] hover:border-[#C4C4C4]"
                  }`}
                >
                  <div className="truncate font-semibold">{s.label}</div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right 5 Cols: Calibration Controls & Execution Terminal */}
        <div className="lg:col-span-5 space-y-4">
          
          <div className="panel-enterprise p-5 space-y-5">
            <div className="border-b border-[#DCDCDC] pb-3">
              <h3 className="text-xs font-bold text-[#171717] uppercase tracking-wider flex items-center gap-2 font-mono">
                <Sliders className="w-3.5 h-3.5 text-[#525252]" />
                Inference Calibration Parameters
              </h3>
              <p className="text-[11px] text-[#525252] mt-0.5">
                Configure optical detection thresholds prior to automated batch execution.
              </p>
            </div>

            {/* Threshold Slider */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-[#525252] font-medium">Cutoff Sensitivity:</span>
                <span className="font-bold text-[#171717] bg-[#EAEAEA] px-2.5 py-0.5 rounded-md border border-[#DCDCDC] font-mono">
                  {(confThreshold * 100).toFixed(0)}% (τ = {confThreshold.toFixed(2)})
                </span>
              </div>

              <input
                type="range"
                min="0.10"
                max="0.90"
                step="0.05"
                value={confThreshold}
                disabled={isScanning}
                onChange={(e) => setConfThreshold(parseFloat(e.target.value))}
                className="w-full accent-[#171717] h-1.5 bg-[#DCDCDC] rounded cursor-pointer"
              />

              <div className="flex justify-between text-[10.5px] font-mono text-[#737373]">
                <span>0.10 (High Recall)</span>
                <span>0.50 (Nominal)</span>
                <span>0.90 (Strict)</span>
              </div>
            </div>

            {/* Technical Specifications Matrix */}
            <div className="space-y-2 text-xs font-mono bg-[#EAEAEA] p-3.5 rounded-xl border border-[#DCDCDC]">
              <div className="flex justify-between text-[#525252]">
                <span>Inspection Protocol:</span>
                <span className="text-[#171717] font-semibold">ASTM D5430 4-Point</span>
              </div>
              <div className="flex justify-between text-[#525252]">
                <span>Neural Architecture:</span>
                <span className="text-[#171717] font-semibold">Faster R-CNN FPN</span>
              </div>
              <div className="flex justify-between text-[#525252]">
                <span>Backbone:</span>
                <span className="text-[#171717] font-semibold">ResNet-50 (41.4M)</span>
              </div>
              <div className="flex justify-between text-[#525252]">
                <span>Defect Classes:</span>
                <span className="text-[#171717] font-semibold">Hole, Knot, Stain</span>
              </div>
              <div className="flex justify-between text-[#525252]">
                <span>Domain Verification:</span>
                <span className="text-[#137333] font-semibold">MobileNetV3 Active</span>
              </div>
            </div>

            {/* Primary Execution CTA */}
            <button
              onClick={triggerInspect}
              disabled={isScanning || (!selectedFile && !isSample)}
              className={`w-full py-3 rounded-lg font-bold text-xs flex items-center justify-center gap-2 transition-all cursor-pointer ${
                isScanning || (!selectedFile && !isSample)
                  ? "bg-[#E2E2E2] text-[#737373] cursor-not-allowed border border-[#DCDCDC]"
                  : "bg-[#171717] hover:bg-[#262626] text-[#F5F5F5] shadow-sm"
              }`}
            >
              {isScanning ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Processing Inspection Pipeline...</span>
                </>
              ) : (
                <>
                  <ScanLine className="w-4 h-4" />
                  <span>Execute Optical Inspection Run</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>

        </div>

      </div>

    </div>
  );
}
