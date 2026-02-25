import { DocsLayout } from "fumadocs-ui/layouts/docs";
import { RootProvider } from "fumadocs-ui/provider/next";
import { source } from "@/lib/source";
import type { ReactNode } from "react";

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <RootProvider>
      <DocsLayout
        tree={source.pageTree}
        nav={{
          title: "civ6-mcp",
          url: "/",
        }}
        links={[
          { text: "Games", url: "/games", active: "url" },
          { text: "CivBench", url: "/civbench", active: "url" },
          { text: "About", url: "/about", active: "url" },
        ]}
        sidebar={{
          collapsible: true,
          defaultOpenLevel: 1,
        }}
      >
        {children}
      </DocsLayout>
    </RootProvider>
  );
}
