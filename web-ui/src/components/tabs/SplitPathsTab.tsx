"use client";

import React, { useState } from "react";
import { RotateCcw } from "lucide-react";
import { FileDropZone } from "@/components/shared/FileDropZone";
import { StatusBanner } from "@/components/shared/StatusBanner";
import { DownloadButton } from "@/components/shared/DownloadButton";
import { ProgressIndicator } from "@/components/shared/ProgressIndicator";
import { apiSplitPaths } from "@/lib/api";
import type { SplitPathsStats } from "@/lib/types";

type Stage = "upload" | "processing" | "done";

export function SplitPathsTab() {
  const [stage, setStage] = useState<Stage>("upload");
  const [svgFile, setSvgFile] = useState<File | null>(null);
  const [result, setResult] = useState<Blob | null>(null);
  const [stats, setStats] = useState<SplitPathsStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleProcess() {
    if (!svgFile) return;
    setStage("processing");
    setError(null);
    try {
      const { blob, stats: s } = await apiSplitPaths(svgFile);
      setResult(blob);
      setStats(s);
      setStage("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Split paths failed.");
      setStage("upload");
    }
  }

  function handleReset() {
    setSvgFile(null);
    setResult(null);
    setStats(null);
    setError(null);
    setStage("upload");
  }

  const stem = svgFile?.name?.replace(/\.svg$/i, "") ?? "output";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.25rem" }}>
          Split Paths
        </h1>
        <p style={{ color: "var(--color-text-secondary)", fontSize: "0.9375rem" }}>
          Split compound SVG paths (multiple M commands) into separate{" "}
          <code className="mono">&lt;path&gt;</code> elements, preserving donut holes.
        </p>
      </div>

      {stage !== "processing" && (
        <div className="card" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <FileDropZone
            accept=".svg"
            multiple={false}
            onFilesSelected={(files) => { setSvgFile(files[0] ?? null); setError(null); }}
            selectedFiles={svgFile ? [svgFile] : []}
            label="Drop an SVG file here, or click to browse"
          />
          {error && <StatusBanner variant="error" title="Error" message={error} />}
          {stage === "upload" && (
            <button
              className="btn btn-primary"
              onClick={handleProcess}
              disabled={!svgFile}
              style={{ alignSelf: "flex-start" }}
            >
              Split Paths
            </button>
          )}
        </div>
      )}

      {stage === "processing" && (
        <div className="card">
          <ProgressIndicator message="Splitting paths…" />
        </div>
      )}

      {stage === "done" && result && stats && (
        <div className="card" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <StatusBanner
            variant="success"
            title="Paths split successfully!"
            message="The output SVG has been generated."
          />

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: "0.75rem",
              textAlign: "center",
            }}
          >
            {[
              { label: "Paths Processed", value: stats.paths_processed },
              { label: "Subpaths Created", value: stats.subpaths_created },
              { label: "Holes Preserved", value: stats.holes_preserved },
            ].map(({ label, value }) => (
              <div
                key={label}
                style={{
                  padding: "0.75rem",
                  backgroundColor: "var(--color-bg)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "var(--radius-md)",
                }}
              >
                <p style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--color-accent)" }}>
                  {value}
                </p>
                <p style={{ fontSize: "0.75rem", color: "var(--color-text-secondary)" }}>{label}</p>
              </div>
            ))}
          </div>

          <div style={{ display: "flex", gap: "0.75rem" }}>
            <DownloadButton blob={result} filename={`${stem}-split.svg`} />
            <button className="btn btn-secondary" onClick={handleReset}>
              <RotateCcw size={14} /> Start Over
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
