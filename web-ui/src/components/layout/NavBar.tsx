"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "./ThemeToggle";

const NAV_LINKS = [
  { href: "/create", label: "Create" },
  { href: "/manage", label: "Manage" },
  { href: "/extract", label: "Extract" },
  { href: "/inspect", label: "Inspect" },
  { href: "/validate", label: "Validate" },
  { href: "/split-paths", label: "Split Paths" },
];

export function NavBar() {
  const pathname = usePathname();

  return (
    <header
      style={{
        backgroundColor: "var(--color-surface)",
        borderBottom: "1px solid var(--color-border)",
        position: "sticky",
        top: 0,
        zIndex: 100,
      }}
    >
      <nav
        style={{
          maxWidth: "1100px",
          margin: "0 auto",
          padding: "0 1rem",
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
          height: "3.5rem",
        }}
      >
        <Link
          href="https://github.com/jamesbconner/SVG2DrawIOLib"
          style={{
            fontWeight: 700,
            fontSize: "1rem",
            color: "var(--color-text-primary)",
            textDecoration: "none",
            marginRight: "1rem",
            whiteSpace: "nowrap",
          }}
        >
          SVG2DrawIOLib
        </Link>

        <div style={{ display: "flex", gap: "0.25rem", flex: 1, overflowX: "auto" }}>
          {NAV_LINKS.map(({ href, label }) => {
            const isActive = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                style={{
                  padding: "0.375rem 0.75rem",
                  borderRadius: "var(--radius-md)",
                  fontSize: "0.875rem",
                  fontWeight: isActive ? 600 : 400,
                  color: isActive ? "var(--color-accent)" : "var(--color-text-secondary)",
                  backgroundColor: isActive ? "var(--color-bg)" : "transparent",
                  textDecoration: "none",
                  whiteSpace: "nowrap",
                  transition: "color 0.15s, background-color 0.15s",
                }}
              >
                {label}
              </Link>
            );
          })}
        </div>

        <ThemeToggle />
      </nav>
    </header>
  );
}
