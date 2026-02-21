"use client";

import React, { useState } from "react";
import { RotateCcw } from "lucide-react";
import { FileDropZone } from "@/components/shared/FileDropZone";
import { StatusBanner } from "@/components/shared/StatusBanner";
import { DownloadButton } from "@/components/shared/DownloadButton";
import { ProgressIndicator } from "@/components/shared/ProgressIndicator";
import { IconList } from "@/components/shared/IconList";
import { apiExtract, apiList } from "@/lib/api";

type Stage = "upload" | "select" | "processing" | "done";

export function ExtractTab() {
  const [stage, setStage] = useState<Stage>("upload");
  const [libraryFile, setLibraryFile] = useState<File | null>(null);
  const [iconNames, setIconNames] = useState<string[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [result, setResult] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingList, setLoadingList] = useState(false);

  async function handleFileSelected(files: File[]) {
    const file = files[0] ?? null;
    setLibraryFile(file);
    setIconNames([]);
    setSelected([]);
    setResult(null);
    setError(null);

    if (!file) { setStage("upload"); return; }

    setLoadingList(true);
    try {
      const data = await apiList(file);
      setIconNames(data.icon_names);
      setStage("select");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to list icons.");
    } finally {
      setLoadingList(false);
    }
  }

  async function handleExtract() {
    if (!libraryFile) return;
    setStage("processing");
    setError(null);
    try {
      const blob = await apiExtract(libraryFile, selected);
      setResult(blob);
      setStage("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Extraction failed.");
      setStage("select");
    }
  }

  function handleReset() {
    setLibraryFile(null);
    setIconNames([]);
    setSelected([]);
    setResult(null);
    setError(null);
    setStage("upload");
  }

  const archiveName = `${libraryFile?.name?.replace(".xml", "") ?? "icons"}-icons.zip`;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.25rem" }}>
          Extract Icons
        </h1>
        <p style={{ color: "var(--color-text-secondary)", fontSize: "0.9375rem" }}>
          Extract icons from a DrawIO library as individual SVG files in a ZIP archive.
        </p>
      </div>

      <div className="card">
        <FileDropZone
          accept=".xml"
          multiple={false}
          onFilesSelected={handleFileSelected}
          selectedFiles={libraryFile ? [libraryFile] : []}
          label="Drop a DrawIO library (.xml) here, or click to browse"
        />
        {loadingList && <ProgressIndicator message="Loading icon list…" />}
      </div>

      {stage === "select" && (
        <div className="card" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <h2 style={{ fontSize: "1rem", fontWeight: 600 }}>
            Select Icons ({iconNames.length} available)
          </h2>
          <p style={{ fontSize: "0.8125rem", color: "var(--color-text-secondary)" }}>
            Leave all unselected to extract every icon.
          </p>
          <IconList
            iconNames={iconNames}
            selected={selected}
            onSelectionChange={setSelected}
            showSelectAll
          />
          {error && <StatusBanner variant="error" title="Error" message={error} />}
          <div style={{ display: "flex", gap: "0.75rem" }}>
            <button className="btn btn-primary" onClick={handleExtract}>
              Extract {selected.length > 0 ? `${selected.length} Icons` : "All Icons"}
            </button>
            <button className="btn btn-secondary" onClick={handleReset}>
              <RotateCcw size={14} /> Reset
            </button>
          </div>
        </div>
      )}

      {stage === "processing" && (
        <div className="card">
          <ProgressIndicator message="Extracting icons…" />
        </div>
      )}

      {stage === "done" && result && (
        <div className="card" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <StatusBanner
            variant="success"
            title="Extraction complete!"
            message={`Icons packaged into ${archiveName}.`}
          />
          <div style={{ display: "flex", gap: "0.75rem" }}>
            <DownloadButton blob={result} filename={archiveName} />
            <button className="btn btn-secondary" onClick={handleReset}>
              <RotateCcw size={14} /> Start Over
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
