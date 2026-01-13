/**
 * ============================================
 * openCowork 根布局
 * ============================================
 * 这个文件定义了整个应用的"外壳"：
 * - HTML 结构
 * - 全局字体
 * - SEO 元数据
 */

import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

// 加载 Google 字体（Geist 是一款现代等宽字体）
const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

// SEO 元数据
export const metadata: Metadata = {
  title: "openCowork - 开源 AI 桌面助手",
  description: "让 AI 看懂你的屏幕，帮你完成重复性工作。支持 OpenAI、Gemini、Claude。",
  keywords: ["AI", "桌面助手", "Computer Use", "OpenAI", "Gemini", "Claude", "自动化"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    // 默认启用暗色模式
    <html lang="zh-CN" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
