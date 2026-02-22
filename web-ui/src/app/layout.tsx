import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/context/ThemeContext";
import { AppStateProvider } from "@/context/AppStateContext";
import { NavBar } from "@/components/layout/NavBar";

export const metadata: Metadata = {
  title: "SVG2DrawIO — Shape Library Builder",
  description: "Convert SVG files into DrawIO shape libraries from your browser.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider>
          <AppStateProvider>
            <NavBar />
            <main
              style={{
                maxWidth: "1100px",
                margin: "0 auto",
                padding: "2rem 1rem",
              }}
            >
              {children}
            </main>
          </AppStateProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
