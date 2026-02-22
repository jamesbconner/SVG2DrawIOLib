"use client";

import React, { useState } from "react";
import { CheckCircle, XCircle } from "lucide-react";
import { FileDropZone } from "@/components/shared/FileDropZone";
import { StatusBanner } from "@/components/shared/StatusBanner";
import { ProgressIndicator } from "@/components/shared/ProgressIndicator";
import { apiValidate } from "@/lib/api";
import type { ValidateResponse } from "@/lib/types";

export function ValidateTab() {
  const [libraryFile, setLibraryFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ValidateResponse | null>(null);

  async function handleValidate() {
    if (!libraryFile) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await apiValidate(libraryFile);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Validation request failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.25rem" }}>
          Validate Library
        </h1>
        <p style={{ color: "var(--color-text-secondary)", fontSize: "0.9375rem" }}>
          Check a DrawIO library for structural and content integrity issues.
        </p>
      </div>

      <div className="card" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        <FileDropZone
          accept=".xml"
          multiple={false}
          onFilesSelected={(files) => { setLibraryFile(files[0] ?? null); setResult(null); }}
          selectedFiles={libraryFile ? [libraryFile] : []}
          label="Drop a DrawIO library (.xml) here, or click to browse"
        />
        <button
          className="btn btn-primary"
          onClick={handleValidate}
          disabled={!libraryFile || loading}
          style={{ alignSelf: "flex-start" }}
        >
          Validate
        </button>
      </div>

      {loading && (
        <div className="card">
          <ProgressIndicator message="Validating library…" />
        </div>
      )}

      {error && <StatusBanner variant="error" title="Request failed" message={error} />}

      {result && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {/* Overall badge */}
          <div className="card" style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            {result.valid ? (
              <CheckCircle size={24} style={{ color: "var(--color-success)" }} />
            ) : (
              <XCircle size={24} style={{ color: "var(--color-error)" }} />
            )}
            <div>
              <span className={`badge ${result.valid ? "badge-success" : "badge-error"}`} style={{ fontSize: "0.9375rem" }}>
                {result.valid ? "Valid" : "Invalid"}
              </span>
              <p style={{ fontSize: "0.875rem", color: "var(--color-text-secondary)", marginTop: "0.25rem" }}>
                {result.checks.icon_count} icons — {result.checks.icons_validated} valid, {result.checks.icons_failed} failed
              </p>
            </div>
          </div>

          {/* Checks table */}
          <div className="card">
            <h2 style={{ fontSize: "1rem", fontWeight: 600, marginBottom: "0.75rem" }}>Checks</h2>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
              <tbody>
                {[
                  { label: "XML Structure", pass: result.checks.xml_structure },
                  { label: "JSON Format", pass: result.checks.json_format },
                  {
                    label: `Icon Validation (${result.checks.icons_validated}/${result.checks.icon_count})`,
                    pass: result.checks.icons_failed === 0,
                  },
                ].map(({ label, pass }) => (
                  <tr key={label} style={{ borderBottom: "1px solid var(--color-border)" }}>
                    <td style={{ padding: "0.5rem 0.25rem", color: "var(--color-text-secondary)" }}>{label}</td>
                    <td style={{ padding: "0.5rem 0.25rem", textAlign: "right" }}>
                      <span className={`badge ${pass ? "badge-success" : "badge-error"}`}>
                        {pass ? "Pass" : "Fail"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Errors & Warnings */}
          {(result.errors.length > 0 || result.warnings.length > 0) && (
            <div className="card" style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              {result.errors.map((e, i) => (
                <StatusBanner key={i} variant="error" message={e} />
              ))}
              {result.warnings.map((w, i) => (
                <StatusBanner key={i} variant="warning" message={w} />
              ))}
            </div>
          )}

          {/* Icon Issues */}
          {result.icon_issues.length > 0 && (
            <div className="card">
              <h2 style={{ fontSize: "1rem", fontWeight: 600, marginBottom: "0.75rem" }}>
                Icon Issues ({result.icon_issues.length})
              </h2>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8125rem" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--color-border)" }}>
                    <th style={{ padding: "0.5rem 0.25rem", textAlign: "left", fontWeight: 600 }}>Severity</th>
                    <th style={{ padding: "0.5rem 0.25rem", textAlign: "left", fontWeight: 600 }}>Icon</th>
                    <th style={{ padding: "0.5rem 0.25rem", textAlign: "left", fontWeight: 600 }}>Message</th>
                  </tr>
                </thead>
                <tbody>
                  {result.icon_issues.map((issue, i) => (
                    <tr key={i} style={{ borderBottom: "1px solid var(--color-border)" }}>
                      <td style={{ padding: "0.5rem 0.25rem" }}>
                        <span className={`badge ${issue.severity === "error" ? "badge-error" : "badge-warning"}`}>
                          {issue.severity}
                        </span>
                      </td>
                      <td style={{ padding: "0.5rem 0.25rem" }} className="mono">{issue.icon}</td>
                      <td style={{ padding: "0.5rem 0.25rem", color: "var(--color-text-secondary)" }}>{issue.message}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
