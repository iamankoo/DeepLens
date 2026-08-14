import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // This workspace directory holds many unrelated sibling projects, one of
  // which left a stray package-lock.json at its root; without this, Next.js
  // infers that as the monorepo root instead of frontend/. Pin it explicitly.
  outputFileTracingRoot: path.join(__dirname),
};

export default nextConfig;
