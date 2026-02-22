"use client";

import React, { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import type { ProcessingOptions } from "@/lib/types";

interface ProcessingOptionsFormProps {
  value: ProcessingOptions;
  onChange: (opts: ProcessingOptions) => void;
  collapsed?: boolean;
}

export function ProcessingOptionsForm({
  value,
  onChange,
  collapsed = true,
}: ProcessingOptionsFormProps) {
  const [open, setOpen] = useState(!collapsed);

  function update<K extends keyof ProcessingOptions>(key: K, val: ProcessingOptions[K]) {
    onChange({ ...value, [key]: val });
  }

  return (
    <div style={{ border: "1px solid var(--color-border)", borderRadius: "var(--radius-md)" }}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0.625rem 0.875rem",
          background: "none",
          border: "none",
          cursor: "pointer",
          color: "var(--color-text-primary)",
          fontWeight: 500,
          fontSize: "0.875rem",
        }}
      >
        <span>CSS / Processing Options</span>
        {open ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
      </button>

      {open && (
        <div
          style={{
            padding: "0.875rem",
            borderTop: "1px solid var(--color-border)",
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
            gap: "0.875rem",
          }}
        >
          <div className="form-group" style={{ gridColumn: "1 / -1" }}>
            <label className="checkbox-group">
              <input
                type="checkbox"
                checked={value.add_css}
                onChange={(e) => update("add_css", e.target.checked)}
              />
              <span className="form-label">Inject CSS classes</span>
            </label>
            <span className="form-hint">Enables color editing in DrawIO via CSS class injection.</span>
          </div>

          {value.add_css && (
            <>
              <div className="form-group">
                <label className="form-label" htmlFor="css_mode">CSS Mode</label>
                <select
                  id="css_mode"
                  className="form-select"
                  value={value.css_mode}
                  onChange={(e) => update("css_mode", e.target.value as ProcessingOptions["css_mode"])}
                >
                  <option value="fill">fill</option>
                  <option value="stroke">stroke</option>
                  <option value="both">both</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="css_color">Fill Color</label>
                <input
                  id="css_color"
                  type="color"
                  className="form-input"
                  value={value.css_color}
                  onChange={(e) => update("css_color", e.target.value)}
                  style={{ height: "2.5rem", padding: "0.25rem 0.5rem" }}
                />
              </div>

              {(value.css_mode === "stroke" || value.css_mode === "both") && (
                <div className="form-group">
                  <label className="form-label" htmlFor="css_stroke_color">Stroke Color</label>
                  <input
                    id="css_stroke_color"
                    type="color"
                    className="form-input"
                    value={value.css_stroke_color}
                    onChange={(e) => update("css_stroke_color", e.target.value)}
                    style={{ height: "2.5rem", padding: "0.25rem 0.5rem" }}
                  />
                </div>
              )}

              <div className="form-group">
                <label className="form-label" htmlFor="css_tag">Target Element</label>
                <input
                  id="css_tag"
                  type="text"
                  className="form-input"
                  value={value.css_tag}
                  onChange={(e) => update("css_tag", e.target.value)}
                  placeholder="path"
                />
              </div>

              <div className="form-group" style={{ gridColumn: "1 / -1" }}>
                <label className="checkbox-group">
                  <input
                    type="checkbox"
                    checked={value.preserve_current_color}
                    onChange={(e) => update("preserve_current_color", e.target.checked)}
                  />
                  <span className="form-label">Preserve currentColor</span>
                </label>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
