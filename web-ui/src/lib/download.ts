/**
 * Trigger a browser download from a Blob by creating a temporary object URL,
 * auto-clicking a hidden anchor, then immediately revoking the URL.
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.style.display = "none";
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  // Revoke after a short delay so the browser has time to initiate the download
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
