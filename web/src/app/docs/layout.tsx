import { DocsLayout } from "fumadocs-ui/layouts/docs";
import { RootProvider } from "fumadocs-ui/provider/next";
import { source } from "@/lib/source";
import { NavBar } from "@/components/nav-bar";
import type { ReactNode } from "react";

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <RootProvider>
      <NavBar active="docs" />
      <DocsLayout
        tree={source.pageTree}
        nav={{
          title: "Docs",
          url: "/docs",
        }}
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
