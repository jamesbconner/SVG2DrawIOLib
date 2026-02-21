import React from "react";

interface ProgressIndicatorProps {
  message?: string;
}

export function ProgressIndicator({ message = "Processing…" }: ProgressIndicatorProps) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "1rem",
        padding: "2rem",
        color: "var(--color-text-secondary)",
      }}
      aria-live="polite"
      aria-busy="true"
    >
      <div
        style={{
          width: "2rem",
          height: "2rem",
          border: "3px solid var(--color-border)",
          borderTopColor: "var(--color-accent)",
          borderRadius: "50%",
          animation: "spin 0.8s linear infinite",
        }}
      />
      <p style={{ fontSize: "0.875rem" }}>{message}</p>
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
