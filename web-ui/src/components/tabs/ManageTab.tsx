"use client";

import React, { useState } from "react";
import { RotateCcw } from "lucide-react";
import { FileDropZone } from "@/components/shared/FileDropZone";
import { StatusBanner } from "@/components/shared/StatusBanner";
import { DownloadButton } from "@/components/shared/DownloadButton";
import { ProgressIndicator } from "@/components/shared/ProgressIndicator";
import { IconList } from "@/components/shared/IconList";
import { ProcessingOptionsForm } from "@/components/forms/ProcessingOptionsForm";
import { SizingOptionsForm } from "@/components/forms/SizingOptionsForm";
import { apiAdd, apiList, apiRemove, apiRename } from "@/lib/api";
import { useAppState } from "@/context/AppStateContext";
import type { ProcessingOptions, SizingOptions } from "@/lib/types";

type SubTab = "add" | "remove" | "rename";

const DEFAULT_OPTS: ProcessingOptions = {
  add_css: true,
  css_mode: "fill",
  css_color: "#000000",
  css_stroke_color: "#000000",
  preserve_current_color: true,
  css_tag: "path",
};

const DEFAULT_SIZING: SizingOptions = { width: null, height: null, max_size: null };

// ─── Add Icons Sub-Tab ────────────────────────────────────────────────────────

function AddIconsTab({
  libraryFile,
  onResult,
}: {
  libraryFile: File;
  onResult: (blob: Blob) => void;
}) {
  const [svgFiles, setSvgFiles] = useState<File[]>([]);
  const [replaceDupes, setReplaceDupes] = useState(false);
  const [addDupes, setAddDupes] = useState(false);
  const [opts, setOpts] = useState<ProcessingOptions>(DEFAULT_OPTS);
  const [sizing, setSizing] = useState<SizingOptions>(DEFAULT_SIZING);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAdd() {
    setLoading(true);
    setError(null);
    try {
      const blob = await apiAdd(libraryFile, svgFiles, replaceDupes, addDupes, opts, sizing);
      onResult(blob);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Add failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
      <div className="card">
        <h3 style={{ fontWeight: 600, marginBottom: "0.75rem" }}>SVG Files to Add</h3>
        <FileDropZone
          accept=".svg"
          multiple
          onFilesSelected={setSvgFiles}
          selectedFiles={svgFiles}
          label="Drop SVG files here, or click to browse"
        />
      </div>

      <div className="card" style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        <h3 style={{ fontWeight: 600 }}>Duplicate Handling</h3>
        <label className="checkbox-group">
          <input type="checkbox" checked={replaceDupes} onChange={(e) => setReplaceDupes(e.target.checked)} />
          <span style={{ fontSize: "0.875rem" }}>Replace existing icons with same name</span>
        </label>
        <label className="checkbox-group">
          <input type="checkbox" checked={addDupes} onChange={(e) => setAddDupes(e.target.checked)} />
          <span style={{ fontSize: "0.875rem" }}>Add duplicates with auto-renamed suffix</span>
        </label>
      </div>

      <div className="card">
        <SizingOptionsForm value={sizing} onChange={setSizing} />
      </div>

      <div className="card">
        <ProcessingOptionsForm value={opts} onChange={setOpts} />
      </div>

      {error && <StatusBanner variant="error" title="Error" message={error} />}
      {loading && <ProgressIndicator message="Adding icons…" />}
      {!loading && (
        <button
          className="btn btn-primary"
          onClick={handleAdd}
          disabled={svgFiles.length === 0}
          style={{ alignSelf: "flex-start" }}
        >
          Add Icons
        </button>
      )}
    </div>
  );
}

// ─── Remove Icons Sub-Tab ─────────────────────────────────────────────────────

function RemoveIconsTab({
  libraryFile,
  iconNames,
  onResult,
}: {
  libraryFile: File;
  iconNames: string[];
  onResult: (blob: Blob, removedCount: number) => void;
}) {
  const [selected, setSelected] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleRemove() {
    if (selected.length === 0) return;
    setLoading(true);
    setError(null);
    try {
      const { blob, removedCount } = await apiRemove(libraryFile, selected);
      onResult(blob, removedCount);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Remove failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
      <div className="card" style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        <h3 style={{ fontWeight: 600 }}>Select Icons to Remove</h3>
        <IconList
          iconNames={iconNames}
          selected={selected}
          onSelectionChange={setSelected}
          showSelectAll
        />
        {error && <StatusBanner variant="error" title="Error" message={error} />}
        {loading && <ProgressIndicator message="Removing icons…" />}
        {!loading && (
          <button
            className="btn btn-danger"
            onClick={handleRemove}
            disabled={selected.length === 0}
            style={{ alignSelf: "flex-start" }}
          >
            Remove {selected.length > 0 ? `${selected.length} Icon${selected.length !== 1 ? "s" : ""}` : "Icons"}
          </button>
        )}
      </div>
    </div>
  );
}

// ─── Rename Icon Sub-Tab ──────────────────────────────────────────────────────

function RenameIconTab({
  libraryFile,
  iconNames,
  onResult,
}: {
  libraryFile: File;
  iconNames: string[];
  onResult: (blob: Blob, wasOverwritten: boolean) => void;
}) {
  const [oldName, setOldName] = useState("");
  const [newName, setNewName] = useState("");
  const [overwrite, setOverwrite] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleRename() {
    if (!oldName || !newName) return;
    setLoading(true);
    setError(null);
    try {
      const { blob, wasOverwritten } = await apiRename(libraryFile, oldName, newName, overwrite);
      onResult(blob, wasOverwritten);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Rename failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
      <h3 style={{ fontWeight: 600 }}>Rename Icon</h3>
      <div className="form-group">
        <label className="form-label" htmlFor="old-name">Current Name</label>
        <select
          id="old-name"
          className="form-select"
          value={oldName}
          onChange={(e) => setOldName(e.target.value)}
        >
          <option value="">— select icon —</option>
          {iconNames.map((n) => (
            <option key={n} value={n}>{n}</option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label className="form-label" htmlFor="new-name">New Name</label>
        <input
          id="new-name"
          type="text"
          className="form-input"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder="Enter new name"
        />
      </div>

      <label className="checkbox-group">
        <input
          type="checkbox"
          checked={overwrite}
          onChange={(e) => setOverwrite(e.target.checked)}
        />
        <span style={{ fontSize: "0.875rem" }}>Overwrite if new name already exists</span>
      </label>

      {error && <StatusBanner variant="error" title="Error" message={error} />}
      {loading && <ProgressIndicator message="Renaming icon…" />}
      {!loading && (
        <button
          className="btn btn-primary"
          onClick={handleRename}
          disabled={!oldName || !newName}
          style={{ alignSelf: "flex-start" }}
        >
          Rename Icon
        </button>
      )}
    </div>
  );
}

// ─── ManageTab ────────────────────────────────────────────────────────────────

type ResultState = {
  blob: Blob;
  message: string;
  filename: string;
} | null;

export function ManageTab() {
  const [subTab, setSubTab] = useState<SubTab>("add");
  const { sharedLibraryFile, sharedIconNames, setSharedLibraryFile, setSharedIconNames } =
    useAppState();
  const [loadingList, setLoadingList] = useState(false);
  const [listError, setListError] = useState<string | null>(null);
  const [result, setResult] = useState<ResultState>(null);

  async function handleLibraryFileSelected(files: File[]) {
    const file = files[0] ?? null;
    setSharedLibraryFile(file);
    setSharedIconNames([]);
    setResult(null);
    setListError(null);

    if (!file) return;

    setLoadingList(true);
    try {
      const data = await apiList(file);
      setSharedIconNames(data.icon_names);
    } catch (err) {
      setListError(err instanceof Error ? err.message : "Failed to list icons.");
    } finally {
      setLoadingList(false);
    }
  }

  function handleReset() {
    setSharedLibraryFile(null);
    setSharedIconNames([]);
    setResult(null);
    setListError(null);
  }

  function handleAddResult(blob: Blob) {
    const name = sharedLibraryFile?.name ?? "library.xml";
    setResult({ blob, message: "Icons added to library.", filename: name });
  }

  function handleRemoveResult(blob: Blob, removedCount: number) {
    const name = sharedLibraryFile?.name ?? "library.xml";
    setResult({ blob, message: `${removedCount} icon${removedCount !== 1 ? "s" : ""} removed.`, filename: name });
  }

  function handleRenameResult(blob: Blob, wasOverwritten: boolean) {
    const name = sharedLibraryFile?.name ?? "library.xml";
    setResult({
      blob,
      message: wasOverwritten ? "Icon renamed (overwritten existing)." : "Icon renamed successfully.",
      filename: name,
    });
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.25rem" }}>
          Manage Library
        </h1>
        <p style={{ color: "var(--color-text-secondary)", fontSize: "0.9375rem" }}>
          Add, remove, or rename icons in an existing DrawIO library.
        </p>
      </div>

      {/* Library file upload */}
      <div className="card">
        <FileDropZone
          accept=".xml"
          multiple={false}
          onFilesSelected={handleLibraryFileSelected}
          selectedFiles={sharedLibraryFile ? [sharedLibraryFile] : []}
          label="Drop a DrawIO library (.xml) here, or click to browse"
        />
        {loadingList && <ProgressIndicator message="Loading icon list…" />}
        {listError && <StatusBanner variant="error" message={listError} />}
        {sharedIconNames.length > 0 && (
          <p style={{ fontSize: "0.8125rem", color: "var(--color-text-secondary)", marginTop: "0.5rem" }}>
            {sharedIconNames.length} icons loaded
          </p>
        )}
      </div>

      {/* Result download */}
      {result && (
        <div className="card" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <StatusBanner variant="success" title="Done!" message={result.message} />
          <div style={{ display: "flex", gap: "0.75rem" }}>
            <DownloadButton blob={result.blob} filename={result.filename} />
            <button className="btn btn-secondary" onClick={() => setResult(null)}>
              Continue Editing
            </button>
            <button className="btn btn-secondary" onClick={handleReset}>
              <RotateCcw size={14} /> Reset
            </button>
          </div>
        </div>
      )}

      {sharedLibraryFile && !result && (
        <>
          {/* Sub-tab navigation */}
          <div style={{ display: "flex", borderBottom: "1px solid var(--color-border)", gap: "0.25rem" }}>
            {(["add", "remove", "rename"] as SubTab[]).map((t) => (
              <button
                key={t}
                onClick={() => setSubTab(t)}
                style={{
                  padding: "0.5rem 1rem",
                  background: "none",
                  border: "none",
                  borderBottom: subTab === t ? "2px solid var(--color-accent)" : "2px solid transparent",
                  color: subTab === t ? "var(--color-accent)" : "var(--color-text-secondary)",
                  fontWeight: subTab === t ? 600 : 400,
                  fontSize: "0.875rem",
                  cursor: "pointer",
                  textTransform: "capitalize",
                  marginBottom: "-1px",
                }}
              >
                {t === "add" ? "Add Icons" : t === "remove" ? "Remove Icons" : "Rename Icon"}
              </button>
            ))}
          </div>

          {subTab === "add" && (
            <AddIconsTab libraryFile={sharedLibraryFile} onResult={handleAddResult} />
          )}
          {subTab === "remove" && (
            <RemoveIconsTab
              libraryFile={sharedLibraryFile}
              iconNames={sharedIconNames}
              onResult={handleRemoveResult}
            />
          )}
          {subTab === "rename" && (
            <RenameIconTab
              libraryFile={sharedLibraryFile}
              iconNames={sharedIconNames}
              onResult={handleRenameResult}
            />
          )}
        </>
      )}
    </div>
  );
}
