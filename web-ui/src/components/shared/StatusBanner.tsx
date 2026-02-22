import React from "react";
import { AlertCircle, AlertTriangle, CheckCircle, Info } from "lucide-react";

type Variant = "success" | "error" | "warning" | "info";

interface StatusBannerProps {
  variant: Variant;
  title?: string;
  message: string;
}

const STYLES: Record<Variant, { bg: string; border: string; color: string; icon: React.ReactNode }> = {
  success: {
    bg: "#f0fdf4",
    border: "#bbf7d0",
    color: "#166534",
    icon: <CheckCircle size={16} />,
  },
  error: {
    bg: "#fef2f2",
    border: "#fecaca",
    color: "#991b1b",
    icon: <AlertCircle size={16} />,
  },
  warning: {
    bg: "#fffbeb",
    border: "#fde68a",
    color: "#92400e",
    icon: <AlertTriangle size={16} />,
  },
  info: {
    bg: "#eff6ff",
    border: "#bfdbfe",
    color: "#1e40af",
    icon: <Info size={16} />,
  },
};

export function StatusBanner({ variant, title, message }: StatusBannerProps) {
  const s = STYLES[variant];
  return (
    <div
      role="alert"
      style={{
        backgroundColor: s.bg,
        border: `1px solid ${s.border}`,
        borderRadius: "var(--radius-md)",
        padding: "0.75rem 1rem",
        color: s.color,
        display: "flex",
        gap: "0.625rem",
        alignItems: "flex-start",
      }}
    >
      <span style={{ marginTop: "0.125rem", flexShrink: 0 }}>{s.icon}</span>
      <div>
        {title && <p style={{ fontWeight: 600, marginBottom: "0.125rem" }}>{title}</p>}
        <p style={{ fontSize: "0.875rem" }}>{message}</p>
      </div>
    </div>
  );
}
