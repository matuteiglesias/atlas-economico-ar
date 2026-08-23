import type { Metadata } from "next";
import "./globals.css";
import "./plot-artifacts.css";
import "./ux-state.css";

export const metadata: Metadata = {
  title: "Argentina Economic Atlas",
  description: "An explorable map of Argentina's economy.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
