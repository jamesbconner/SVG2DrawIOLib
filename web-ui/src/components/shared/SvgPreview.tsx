import React from "react";

interface SvgPreviewProps {
  svgContent: string;
  alt?: string;
  size?: number;
}

/**
 * Safely renders an SVG by base64-encoding it as a data URI.
 * Uses TextEncoder for proper UTF-8 handling (works on server + browser).
 * Never uses dangerouslySetInnerHTML.
 */
function svgToBase64(svgContent: string): string {
  // TextEncoder is available in Node.js 18+ and all modern browsers.
  const bytes = new TextEncoder().encode(svgContent);
  let binary = "";
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

export function SvgPreview({ svgContent, alt = "SVG preview", size = 80 }: SvgPreviewProps) {
  const encoded = svgToBase64(svgContent);
  const src = `data:image/svg+xml;base64,${encoded}`;

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={src}
      alt={alt}
      width={size}
      height={size}
      style={{
        objectFit: "contain",
        backgroundColor: "var(--color-surface)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-md)",
        padding: "0.5rem",
      }}
    />
  );
}
