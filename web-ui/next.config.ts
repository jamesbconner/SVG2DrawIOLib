import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Produce a fully-static export in web-ui/out/ so FastAPI can serve it.
  // When NEXT_PUBLIC_API_URL is empty the frontend makes same-origin /api/* calls.
  output: "export",
  trailingSlash: true,
};

// In dev mode (next dev), proxy /api/* to the FastAPI server so no .env.local is needed.
// Rewrites are not supported in static exports — this block is skipped during `next build`.
if (process.env.NODE_ENV !== "production") {
  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  nextConfig.rewrites = async () => [
    { source: "/api/:path*", destination: `${apiBase}/api/:path*` },
  ];
}

export default nextConfig;
