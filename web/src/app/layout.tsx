import type { Metadata } from "next";
import { Cinzel, Cormorant_Garamond, JetBrains_Mono } from "next/font/google";
import { ThemeProvider } from "next-themes";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ConvexClientProvider } from "@/components/convex-provider";
import { ConsoleEgg } from "@/components/console-egg";
import { Analytics } from "@vercel/analytics/next";
import "./globals.css";

const cinzel = Cinzel({
  variable: "--font-cinzel",
  subsets: ["latin"],
  weight: ["400", "700"],
});

const cormorant = Cormorant_Garamond({
  variable: "--font-cormorant",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

const jetbrains = JetBrains_Mono({
  variable: "--font-jetbrains",
  subsets: ["latin"],
  weight: ["400", "700"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://civ6-mcp.lwilko.com"),
  title: {
    default: "civ6-mcp",
    template: "%s | civ6-mcp",
  },
  description:
    "An MCP environment for evaluating LLM agents in Civilization VI",
  openGraph: {
    type: "website",
    siteName: "civ6-mcp",
    title: "civ6-mcp",
    description:
      "An MCP environment for evaluating LLM agents in Civilization VI",
  },
  twitter: {
    card: "summary_large_image",
    title: "civ6-mcp",
    description:
      "An MCP environment for evaluating LLM agents in Civilization VI",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${cinzel.variable} ${cormorant.variable} ${jetbrains.variable} antialiased`}
      >
        <ConvexClientProvider>
          <ThemeProvider
            attribute="class"
            defaultTheme="light"
            enableSystem={false}
          >
            <TooltipProvider>
              <ConsoleEgg />
              {children}
            </TooltipProvider>
          </ThemeProvider>
        </ConvexClientProvider>
        <Analytics />
      </body>
    </html>
  );
}
