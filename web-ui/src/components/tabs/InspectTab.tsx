"use client";

import React, { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { FileDropZone } from "@/components/shared/FileDropZone";
import { StatusBanner } from "@/components/shared/StatusBanner";
import { ProgressIndicator } from "@/components/shared/ProgressIndicator";
import { SvgPreview } from "@/components/shared/SvgPreview";
import { apiInspect } from "@/lib/api";
import type { IconInfo, InspectResponse } from "@/lib/types";

function IconCard({ icon }: { icon: IconInfo }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className="card"
      style={{ display: "flex", flexDirection: "column", gap: "0.75rem", padding: "1rem" }}
    >
      <div style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start" }}>
        {icon.svg_content && <SvgPreview svgContent={icon.svg_content} alt={icon.name} size={64} />}
        <div style={{ flex: 1, minWidth: 0 }}>
          <p className="mono" style={{ fontWeight: 600, fontSize: "0.875rem", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {icon.name}
          </p>
          <p style={{ fontSize: "0.75rem", color: "var(--color-text-secondary)", marginTop: "0.125rem" }}>
            {icon.width} × {icon.height} px
          </p>
          {icon.css_classes.length > 0 && (
            <p style={{ fontSize: "0.75rem", color: "var(--color-text-secondary)", marginTop: "0.125rem" }}>
              CSS: {icon.css_classes.join(", ")}
            </p>
          )}
        </div>
      </div>

      {icon.svg_content && (
        <div>
          <button
            type="button"
            onClick={() => setExpanded((e) => !e)}
            style={{
              background: "none",
              border: "none",
              cursor: "pointer",
              fontSize: "0.75rem",
              color: "var(--color-accent)",
              display: "flex",
              alignItems: "center",
              gap: "0.25rem",
              padding: 0,
            }}
          >
            {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
            {expanded ? "Hide" : "Show"} SVG source
          </button>
          {expanded && (
            <pre
              className="mono"
              style={{
                marginTop: "0.5rem",
                padding: "0.75rem",
                backgroundColor: "var(--color-bg)",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-md)",
                fontSize: "0.6875rem",
                overflowX: "auto",
                whiteSpace: "pre-wrap",
                wordBreak: "break-all",
                maxHeight: "200px",
                overflowY: "auto",
              }}
            >
              {icon.svg_content}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}

export function InspectTab() {
  const [libraryFile, setLibraryFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<InspectResponse | null>(null);

  async function handleInspect(file: File) {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await apiInspect(file, [], true);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Inspect request failed.");
    } finally {
      setLoading(false);
    }
  }

  function handleFileSelected(files: File[]) {
    const file = files[0] ?? null;
    setLibraryFile(file);
    setResult(null);
    setError(null);
    if (file) handleInspect(file);
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.25rem" }}>
          Inspect Library
        </h1>
        <p style={{ color: "var(--color-text-secondary)", fontSize: "0.9375rem" }}>
          View icon cards with SVG previews, dimensions, and CSS class information.
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
      </div>

      {loading && (
        <div className="card">
          <ProgressIndicator message="Inspecting library…" />
        </div>
      )}

      {error && <StatusBanner variant="error" title="Request failed" message={error} />}

      {result && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <p style={{ fontSize: "0.875rem", color: "var(--color-text-secondary)" }}>
            {result.count} icon{result.count !== 1 ? "s" : ""} found
          </p>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
              gap: "0.75rem",
            }}
          >
            {result.icons.map((icon) => (
              <IconCard key={icon.name} icon={icon} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
