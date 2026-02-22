"use client";

import React from "react";
import type { SizingOptions } from "@/lib/types";

interface SizingOptionsFormProps {
  value: SizingOptions;
  onChange: (opts: SizingOptions) => void;
}

export function SizingOptionsForm({ value, onChange }: SizingOptionsFormProps) {
  function update<K extends keyof SizingOptions>(key: K, val: SizingOptions[K]) {
    onChange({ ...value, [key]: val });
  }

  function parseOptionalFloat(s: string): number | null {
    const n = parseFloat(s);
    return isNaN(n) ? null : n;
  }

  const mode: "default" | "maxsize" | "fixed" =
    value.width !== null && value.height !== null
      ? "fixed"
      : value.max_size !== null
        ? "maxsize"
        : "default";

  function setMode(m: "default" | "maxsize" | "fixed") {
    if (m === "default") onChange({ width: null, height: null, max_size: null });
    else if (m === "maxsize") onChange({ width: null, height: null, max_size: 40 });
    else onChange({ width: 40, height: 40, max_size: null });
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
      <div className="form-group">
        <label className="form-label">Sizing Mode</label>
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          {(["default", "maxsize", "fixed"] as const).map((m) => (
            <label key={m} className="checkbox-group" style={{ cursor: "pointer" }}>
              <input
                type="radio"
                name="sizing-mode"
                checked={mode === m}
                onChange={() => setMode(m)}
                style={{ accentColor: "var(--color-accent)" }}
              />
              <span style={{ fontSize: "0.875rem" }}>
                {m === "default" && "Default (max 40px)"}
                {m === "maxsize" && "Max dimension"}
                {m === "fixed" && "Fixed W×H"}
              </span>
            </label>
          ))}
        </div>
      </div>

      {mode === "maxsize" && (
        <div className="form-group" style={{ maxWidth: "200px" }}>
          <label className="form-label" htmlFor="max_size">Max Dimension (px)</label>
          <input
            id="max_size"
            type="number"
            className="form-input"
            min={1}
            value={value.max_size ?? ""}
            onChange={(e) => update("max_size", parseOptionalFloat(e.target.value))}
          />
        </div>
      )}

      {mode === "fixed" && (
        <div style={{ display: "flex", gap: "0.75rem", alignItems: "flex-end" }}>
          <div className="form-group" style={{ flex: 1 }}>
            <label className="form-label" htmlFor="width">Width (px)</label>
            <input
              id="width"
              type="number"
              className="form-input"
              min={1}
              value={value.width ?? ""}
              onChange={(e) => update("width", parseOptionalFloat(e.target.value))}
            />
          </div>
          <span style={{ paddingBottom: "0.5rem", color: "var(--color-text-secondary)" }}>×</span>
          <div className="form-group" style={{ flex: 1 }}>
            <label className="form-label" htmlFor="height">Height (px)</label>
            <input
              id="height"
              type="number"
              className="form-input"
              min={1}
              value={value.height ?? ""}
              onChange={(e) => update("height", parseOptionalFloat(e.target.value))}
            />
          </div>
        </div>
      )}
    </div>
  );
}
