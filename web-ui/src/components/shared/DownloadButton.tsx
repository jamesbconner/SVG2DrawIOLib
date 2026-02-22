"use client";

import { Download } from "lucide-react";
import { downloadBlob } from "@/lib/download";

interface DownloadButtonProps {
  blob: Blob;
  filename: string;
  label?: string;
}

export function DownloadButton({ blob, filename, label }: DownloadButtonProps) {
  return (
    <button
      className="btn btn-primary"
      onClick={() => downloadBlob(blob, filename)}
    >
      <Download size={16} />
      {label ?? `Download ${filename}`}
    </button>
  );
}
