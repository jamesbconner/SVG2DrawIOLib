import type {
  InspectResponse,
  ListResponse,
  ProcessingOptions,
  SizingOptions,
  SplitPathsStats,
  ValidateResponse,
} from "./types";

// In dev mode (next dev), rewrites in next.config.ts proxy /api/* to FastAPI.
// In production (static export served by FastAPI), relative URLs hit the same server.
// Set NEXT_PUBLIC_API_URL to an absolute URL only when the API is on a different origin.
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

/** Typed API error containing HTTP status and server detail message. */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

async function checkResponse(res: Response): Promise<void> {
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // ignore parse error
    }
    throw new ApiError(res.status, detail);
  }
}

function appendProcessingOptions(form: FormData, opts: ProcessingOptions): void {
  form.append("add_css", String(opts.add_css));
  form.append("css_mode", opts.css_mode);
  form.append("css_color", opts.css_color);
  form.append("css_stroke_color", opts.css_stroke_color);
  form.append("preserve_current_color", String(opts.preserve_current_color));
  form.append("css_tag", opts.css_tag);
}

function appendSizingOptions(form: FormData, sizing: SizingOptions): void {
  if (sizing.width !== null) form.append("width", String(sizing.width));
  if (sizing.height !== null) form.append("height", String(sizing.height));
  if (sizing.max_size !== null) form.append("max_size", String(sizing.max_size));
}

/** Create a new DrawIO library from SVG files. Returns the library XML as a Blob. */
export async function apiCreate(
  svgFiles: File[],
  outputName: string,
  opts: ProcessingOptions,
  sizing: SizingOptions,
): Promise<Blob> {
  const form = new FormData();
  svgFiles.forEach((f) => form.append("svg_files", f));
  form.append("output_name", outputName);
  appendProcessingOptions(form, opts);
  appendSizingOptions(form, sizing);

  const res = await fetch(`${API_BASE}/api/create`, { method: "POST", body: form });
  await checkResponse(res);
  return res.blob();
}

/** Add SVG icons to an existing library. Returns updated library XML as a Blob. */
export async function apiAdd(
  libraryFile: File,
  svgFiles: File[],
  replaceDupes: boolean,
  addDupes: boolean,
  opts: ProcessingOptions,
  sizing: SizingOptions,
): Promise<Blob> {
  const form = new FormData();
  form.append("library_file", libraryFile);
  svgFiles.forEach((f) => form.append("svg_files", f));
  form.append("replace_duplicates", String(replaceDupes));
  form.append("add_duplicates", String(addDupes));
  appendProcessingOptions(form, opts);
  appendSizingOptions(form, sizing);

  const res = await fetch(`${API_BASE}/api/add`, { method: "POST", body: form });
  await checkResponse(res);
  return res.blob();
}

/** Remove icons from a library. Returns updated library and count removed. */
export async function apiRemove(
  libraryFile: File,
  iconNames: string[],
): Promise<{ blob: Blob; removedCount: number }> {
  const form = new FormData();
  form.append("library_file", libraryFile);
  form.append("icon_names", JSON.stringify(iconNames));

  const res = await fetch(`${API_BASE}/api/remove`, { method: "POST", body: form });
  await checkResponse(res);
  const removedCount = parseInt(res.headers.get("X-Icons-Removed") ?? "0", 10);
  const blob = await res.blob();
  return { blob, removedCount };
}

/** Rename an icon in a library. Returns updated library and whether an icon was overwritten. */
export async function apiRename(
  libraryFile: File,
  oldName: string,
  newName: string,
  overwrite: boolean,
): Promise<{ blob: Blob; wasOverwritten: boolean }> {
  const form = new FormData();
  form.append("library_file", libraryFile);
  form.append("old_name", oldName);
  form.append("new_name", newName);
  form.append("overwrite", String(overwrite));

  const res = await fetch(`${API_BASE}/api/rename`, { method: "POST", body: form });
  await checkResponse(res);
  const wasOverwritten = res.headers.get("X-Icon-Was-Overwritten") === "true";
  const blob = await res.blob();
  return { blob, wasOverwritten };
}

/** List icon names in a library. */
export async function apiList(libraryFile: File): Promise<ListResponse> {
  const form = new FormData();
  form.append("library_file", libraryFile);

  const res = await fetch(`${API_BASE}/api/list`, { method: "POST", body: form });
  await checkResponse(res);
  return res.json() as Promise<ListResponse>;
}

/** Extract icons from a library as a ZIP blob. Pass empty array for all icons. */
export async function apiExtract(libraryFile: File, iconNames: string[]): Promise<Blob> {
  const form = new FormData();
  form.append("library_file", libraryFile);
  form.append("icon_names", JSON.stringify(iconNames));

  const res = await fetch(`${API_BASE}/api/extract`, { method: "POST", body: form });
  await checkResponse(res);
  return res.blob();
}

/** Inspect icons in a library. Pass empty array for all icons. */
export async function apiInspect(
  libraryFile: File,
  iconNames: string[],
  includeSvg: boolean,
): Promise<InspectResponse> {
  const form = new FormData();
  form.append("library_file", libraryFile);
  form.append("icon_names", JSON.stringify(iconNames));
  form.append("include_svg", String(includeSvg));

  const res = await fetch(`${API_BASE}/api/inspect`, { method: "POST", body: form });
  await checkResponse(res);
  return res.json() as Promise<InspectResponse>;
}

/** Validate a library. Always returns HTTP 200; check `valid` field. */
export async function apiValidate(libraryFile: File): Promise<ValidateResponse> {
  const form = new FormData();
  form.append("library_file", libraryFile);

  const res = await fetch(`${API_BASE}/api/validate`, { method: "POST", body: form });
  await checkResponse(res);
  return res.json() as Promise<ValidateResponse>;
}

/** Split compound SVG paths. Returns the modified SVG blob and stats. */
export async function apiSplitPaths(
  svgFile: File,
): Promise<{ blob: Blob; stats: SplitPathsStats }> {
  const form = new FormData();
  form.append("svg_file", svgFile);

  const res = await fetch(`${API_BASE}/api/split-paths`, { method: "POST", body: form });
  await checkResponse(res);

  const stats: SplitPathsStats = {
    paths_processed: parseInt(res.headers.get("X-Paths-Processed") ?? "0", 10),
    subpaths_created: parseInt(res.headers.get("X-Subpaths-Created") ?? "0", 10),
    holes_preserved: parseInt(res.headers.get("X-Holes-Preserved") ?? "0", 10),
  };

  const blob = await res.blob();
  return { blob, stats };
}
