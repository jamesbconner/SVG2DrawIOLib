/** Health check response from /api/health */
export interface HealthResponse {
  status: string;
  version: string;
}

/** Response from /api/list */
export interface ListResponse {
  icon_names: string[];
  count: number;
}

/** A single icon issue from validation */
export interface IconIssue {
  severity: "error" | "warning";
  icon: string;
  message: string;
}

/** Validation checks summary */
export interface ValidationChecks {
  xml_structure: boolean;
  json_format: boolean;
  icon_count: number;
  icons_validated: number;
  icons_failed: number;
}

/** Full validation response from /api/validate */
export interface ValidateResponse {
  valid: boolean;
  errors: string[];
  warnings: string[];
  checks: ValidationChecks;
  icon_issues: IconIssue[];
}

/** Information about a single icon */
export interface IconInfo {
  name: string;
  width: number;
  height: number;
  shape_type: string | null;
  css_classes: string[];
  inline_styles: string | null;
  svg_content: string | null;
}

/** Inspect response from /api/inspect */
export interface InspectResponse {
  icons: IconInfo[];
  count: number;
}

/** Stats returned by /api/split-paths (via headers) */
export interface SplitPathsStats {
  paths_processed: number;
  subpaths_created: number;
  holes_preserved: number;
}

/** Processing options shared across create/add endpoints */
export interface ProcessingOptions {
  add_css: boolean;
  css_mode: "fill" | "stroke" | "both";
  css_color: string;
  css_stroke_color: string;
  preserve_current_color: boolean;
  css_tag: string;
}

/** Sizing options for create/add endpoints */
export interface SizingOptions {
  width: number | null;
  height: number | null;
  max_size: number | null;
}
