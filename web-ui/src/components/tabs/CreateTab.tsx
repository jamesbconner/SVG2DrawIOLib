"use client";

import React, { useState } from "react";
import { RotateCcw } from "lucide-react";
import { FileDropZone } from "@/components/shared/FileDropZone";
import { StatusBanner } from "@/components/shared/StatusBanner";
import { DownloadButton } from "@/components/shared/DownloadButton";
import { ProgressIndicator } from "@/components/shared/ProgressIndicator";
import { ProcessingOptionsForm } from "@/components/forms/ProcessingOptionsForm";
import { SizingOptionsForm } from "@/components/forms/SizingOptionsForm";
import { apiCreate } from "@/lib/api";
import type { ProcessingOptions, SizingOptions } from "@/lib/types";

type Stage = "upload" | "configure" | "processing" | "done";

const DEFAULT_OPTIONS: ProcessingOptions = {
  add_css: false,
  css_mode: "fill",
  css_color: "#000000",
  css_stroke_color: "#000000",
  preserve_current_color: true,
  css_tag: "path",
};

const DEFAULT_SIZING: SizingOptions = {
  width: null,
  height: null,
  max_size: null,
};

export function CreateTab() {
  const [stage, setStage] = useState<Stage>("upload");
  const [svgFiles, setSvgFiles] = useState<File[]>([]);
  const [outputName, setOutputName] = useState("library");
  const [opts, setOpts] = useState<ProcessingOptions>(DEFAULT_OPTIONS);
  const [sizing, setSizing] = useState<SizingOptions>(DEFAULT_SIZING);
  const [result, setResult] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);

  function handleFilesSelected(files: File[]) {
    setSvgFiles(files);
    if (files.length > 0) setStage("configure");
  }

  async function handleCreate() {
    setStage("processing");
    setError(null);
    try {
      const blob = await apiCreate(svgFiles, outputName, opts, sizing);
      setResult(blob);
      setStage("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred.");
      setStage("configure");
    }
  }

  function handleReset() {
    setSvgFiles([]);
    setOutputName("library");
    setOpts(DEFAULT_OPTIONS);
    setSizing(DEFAULT_SIZING);
    setResult(null);
    setError(null);
    setStage("upload");
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.25rem" }}>
          Create Library
        </h1>
        <p style={{ color: "var(--color-text-secondary)", fontSize: "0.9375rem" }}>
          Upload SVG files and package them into a DrawIO shape library.
        </p>
      </div>

      {stage === "upload" && (
        <div className="card">
          <FileDropZone
            accept=".svg"
            multiple
            onFilesSelected={handleFilesSelected}
            selectedFiles={svgFiles}
            label="Drag & drop SVG files here, or click to browse"
          />
        </div>
      )}

      {stage === "configure" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div className="card">
            <h2 style={{ fontSize: "1rem", fontWeight: 600, marginBottom: "1rem" }}>Files</h2>
            <FileDropZone
              accept=".svg"
              multiple
              onFilesSelected={handleFilesSelected}
              selectedFiles={svgFiles}
            />
          </div>

          <div className="card" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <h2 style={{ fontSize: "1rem", fontWeight: 600 }}>Output</h2>
            <div className="form-group" style={{ maxWidth: "320px" }}>
              <label className="form-label" htmlFor="output-name">Library Name</label>
              <input
                id="output-name"
                type="text"
                className="form-input"
                value={outputName}
                onChange={(e) => setOutputName(e.target.value)}
                placeholder="library"
              />
              <span className="form-hint">Filename stem for the output .xml file.</span>
            </div>
          </div>

          <div className="card" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <h2 style={{ fontSize: "1rem", fontWeight: 600 }}>Sizing</h2>
            <SizingOptionsForm value={sizing} onChange={setSizing} />
          </div>

          <div className="card">
            <ProcessingOptionsForm value={opts} onChange={setOpts} />
          </div>

          {error && <StatusBanner variant="error" title="Error" message={error} />}

          <div style={{ display: "flex", gap: "0.75rem" }}>
            <button
              className="btn btn-primary"
              onClick={handleCreate}
              disabled={svgFiles.length === 0}
            >
              Create Library
            </button>
            <button className="btn btn-secondary" onClick={handleReset}>
              <RotateCcw size={14} /> Reset
            </button>
          </div>
        </div>
      )}

      {stage === "processing" && (
        <div className="card">
          <ProgressIndicator message="Creating library…" />
        </div>
      )}

      {stage === "done" && result && (
        <div className="card" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <StatusBanner
            variant="success"
            title="Library created!"
            message={`${svgFiles.length} icon${svgFiles.length !== 1 ? "s" : ""} packaged successfully.`}
          />
          <div style={{ display: "flex", gap: "0.75rem" }}>
            <DownloadButton blob={result} filename={`${outputName || "library"}.xml`} />
            <button className="btn btn-secondary" onClick={handleReset}>
              <RotateCcw size={14} /> Start Over
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
