import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // GitHub Pages 需要静态导出
  output: "export",

  // GitHub Pages 使用仓库名作为 basePath
  // 例如: https://username.github.io/openCowork/
  basePath: process.env.NODE_ENV === "production" ? "/openCowork" : "",

  // 禁用图片优化（静态导出不支持）
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
