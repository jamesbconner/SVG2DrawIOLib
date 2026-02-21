"use client";

import React, { useRef, useState } from "react";
import { Upload, X } from "lucide-react";

const DEFAULT_MAX_SIZE = 10 * 1024 * 1024; // 10 MB

interface FileDropZoneProps {
  accept?: string;
  multiple?: boolean;
  onFilesSelected: (files: File[]) => void;
  selectedFiles?: File[];
  maxFileSizeBytes?: number;
  label?: string;
}

export function FileDropZone({
  accept,
  multiple = false,
  onFilesSelected,
  selectedFiles = [],
  maxFileSizeBytes = DEFAULT_MAX_SIZE,
  label,
}: FileDropZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [sizeError, setSizeError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function validateAndEmit(files: File[]) {
    const oversized = files.filter((f) => f.size > maxFileSizeBytes);
    if (oversized.length > 0) {
      const mb = (maxFileSizeBytes / (1024 * 1024)).toFixed(0);
      setSizeError(`${oversized.map((f) => f.name).join(", ")} exceed ${mb} MB limit.`);
      return;
    }
    setSizeError(null);
    onFilesSelected(files);
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    validateAndEmit(files);
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? []);
    validateAndEmit(files);
    // Reset input so same file can be re-selected
    e.target.value = "";
  }

  function removeFile(index: number) {
    const updated = selectedFiles.filter((_, i) => i !== index);
    onFilesSelected(updated);
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        style={{
          border: `2px dashed ${isDragging ? "var(--color-accent)" : "var(--color-border)"}`,
          borderRadius: "var(--radius-lg)",
          padding: "2rem",
          textAlign: "center",
          cursor: "pointer",
          backgroundColor: isDragging ? "rgba(37, 99, 235, 0.05)" : "var(--color-surface)",
          transition: "border-color 0.15s, background-color 0.15s",
        }}
      >
        <Upload size={28} style={{ color: "var(--color-text-secondary)", marginBottom: "0.5rem" }} />
        <p style={{ fontSize: "0.875rem", color: "var(--color-text-secondary)" }}>
          {label ?? (multiple ? "Drag & drop SVG files here, or click to browse" : "Drag & drop a file here, or click to browse")}
        </p>
        <p style={{ fontSize: "0.75rem", color: "var(--color-text-secondary)", marginTop: "0.25rem" }}>
          Max {(maxFileSizeBytes / (1024 * 1024)).toFixed(0)} MB per file
        </p>
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={handleChange}
          className="sr-only"
          aria-label={label ?? "File upload"}
        />
      </div>

      {sizeError && (
        <p style={{ fontSize: "0.8125rem", color: "var(--color-error)" }}>{sizeError}</p>
      )}

      {selectedFiles.length > 0 && (
        <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "0.375rem" }}>
          {selectedFiles.map((file, i) => (
            <li
              key={`${file.name}-${i}`}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "0.375rem 0.75rem",
                backgroundColor: "var(--color-surface)",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-md)",
                fontSize: "0.8125rem",
              }}
            >
              <span className="mono" style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {file.name}
              </span>
              <span style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexShrink: 0 }}>
                <span style={{ color: "var(--color-text-secondary)", fontSize: "0.75rem" }}>
                  {(file.size / 1024).toFixed(1)} KB
                </span>
                <button
                  onClick={(e) => { e.stopPropagation(); removeFile(i); }}
                  style={{ background: "none", border: "none", cursor: "pointer", color: "var(--color-text-secondary)", padding: "0.125rem" }}
                  aria-label={`Remove ${file.name}`}
                >
                  <X size={14} />
                </button>
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
