import { createMDX } from "fumadocs-mdx/next";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  devIndicators: false,
};

const withMDX = createMDX();

export default withMDX(nextConfig);
