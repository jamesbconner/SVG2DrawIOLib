"use client";

import React, { useMemo, useState } from "react";
import { Search } from "lucide-react";

interface IconListProps {
  iconNames: string[];
  selected: string[];
  onSelectionChange: (selected: string[]) => void;
  showSelectAll?: boolean;
  placeholder?: string;
}

export function IconList({
  iconNames,
  selected,
  onSelectionChange,
  showSelectAll = true,
  placeholder = "Search icons…",
}: IconListProps) {
  const [query, setQuery] = useState("");

  const filtered = useMemo(
    () => iconNames.filter((n) => n.toLowerCase().includes(query.toLowerCase())),
    [iconNames, query],
  );

  const allFilteredSelected = filtered.length > 0 && filtered.every((n) => selected.includes(n));

  function toggleSelectAll() {
    if (allFilteredSelected) {
      // Deselect all filtered
      const filteredSet = new Set(filtered);
      onSelectionChange(selected.filter((n) => !filteredSet.has(n)));
    } else {
      // Add all filtered
      const merged = Array.from(new Set([...selected, ...filtered]));
      onSelectionChange(merged);
    }
  }

  function toggleOne(name: string) {
    if (selected.includes(name)) {
      onSelectionChange(selected.filter((n) => n !== name));
    } else {
      onSelectionChange([...selected, name]);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
      <div style={{ position: "relative" }}>
        <Search
          size={14}
          style={{
            position: "absolute",
            left: "0.6rem",
            top: "50%",
            transform: "translateY(-50%)",
            color: "var(--color-text-secondary)",
            pointerEvents: "none",
          }}
        />
        <input
          type="text"
          className="form-input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          style={{ paddingLeft: "2rem" }}
        />
      </div>

      {showSelectAll && filtered.length > 0 && (
        <label className="checkbox-group" style={{ paddingBottom: "0.375rem", borderBottom: "1px solid var(--color-border)" }}>
          <input
            type="checkbox"
            checked={allFilteredSelected}
            onChange={toggleSelectAll}
          />
          <span style={{ fontSize: "0.8125rem", fontWeight: 500 }}>
            Select all ({filtered.length})
          </span>
        </label>
      )}

      <div
        style={{
          maxHeight: "240px",
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: "0.25rem",
        }}
      >
        {filtered.length === 0 && (
          <p style={{ fontSize: "0.875rem", color: "var(--color-text-secondary)", padding: "0.5rem 0" }}>
            No icons match your search.
          </p>
        )}
        {filtered.map((name) => (
          <label key={name} className="checkbox-group" style={{ padding: "0.25rem 0.5rem", borderRadius: "var(--radius-sm)", cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={selected.includes(name)}
              onChange={() => toggleOne(name)}
            />
            <span className="mono" style={{ fontSize: "0.8125rem" }}>{name}</span>
          </label>
        ))}
      </div>

      {selected.length > 0 && (
        <p style={{ fontSize: "0.75rem", color: "var(--color-text-secondary)" }}>
          {selected.length} icon{selected.length !== 1 ? "s" : ""} selected
        </p>
      )}
    </div>
  );
}
