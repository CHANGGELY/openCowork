"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

// ============================================
// 国际化配置 (i18n)
// ============================================

const 翻译 = {
  zh: {
    title: "openCowork",
    subtitle: "开源版 AI 桌面助手",
    status_connected: "已连接",
    status_connecting: "连接中",
    status_disconnected: "未连接",
    config_btn: "配置 API",
    config_btn_done: "已配置",
    config_title: "配置 API",
    config_desc: "选择你的 AI 提供商并填入 API Key。数据仅存储在本地。",
    provider_label: "AI 提供商",
    provider_placeholder: "选择提供商",
    apikey_label: "API Key",
    apikey_placeholder: "sk-... 或 AIza...",
    save_btn: "保存配置",
    chat_title: "对话",
    agent_running: "Agent 运行中",
    welcome_title: "准备就绪",
    welcome_desc: "输入你想让 AI 帮你完成的任务，比如\"打开计算器\"或\"在 Google 搜索今天的天气\"。",
    input_placeholder: "输入任务...",
    stop_tooltip: "紧急停止 (Ctrl+Alt+Q)",
    msg_connected: "✅ 已连接到后端服务",
    msg_disconnected: "🔌 与后端的连接已断开，尝试重连...",
    msg_config_first: "⚠️ 请先配置 API Key（点击右上角设置按钮）",
    msg_config_success: "✅ 已配置",
    msg_config_fail: "❌ 配置失败",
    msg_send_fail: "❌ 发送失败",
    msg_stop_sent: "🛑 已发送停止信号",
    devtools_tip: "提示：按 Ctrl+Shift+I 可以打开/关闭 Next.js 开发工具（那是个黑色的浮窗）",
    lang_toggle: "English"
  },
  en: {
    title: "openCowork",
    subtitle: "Open Source AI Desktop Assistant",
    status_connected: "Connected",
    status_connecting: "Connecting",
    status_disconnected: "Disconnected",
    config_btn: "Config API",
    config_btn_done: "Configured",
    config_title: "Configure API",
    config_desc: "Select your AI provider and enter your API Key. Data is stored locally.",
    provider_label: "AI Provider",
    provider_placeholder: "Select Provider",
    apikey_label: "API Key",
    apikey_placeholder: "sk-... or AIza...",
    save_btn: "Save Config",
    chat_title: "Chat",
    agent_running: "Agent Running",
    welcome_title: "Ready",
    welcome_desc: "Enter a task for the AI, e.g., 'Open Calculator' or 'Search weather on Google'.",
    input_placeholder: "Enter task...",
    stop_tooltip: "Emergency Stop (Ctrl+Alt+Q)",
    msg_connected: "✅ Connected to backend",
    msg_disconnected: "🔌 Disconnected from backend, retrying...",
    msg_config_first: "⚠️ Please configure API Key first (Top right settings)",
    msg_config_success: "✅ Configured",
    msg_config_fail: "❌ Configuration failed",
    msg_send_fail: "❌ Send failed",
    msg_stop_sent: "🛑 Stop signal sent",
    devtools_tip: "Tip: Press Ctrl+Shift+I to toggle Next.js DevTools (the black overlay)",
    lang_toggle: "中文"
  }
};

type 语言类型 = "zh" | "en";

// ============================================
// 类型定义
// ============================================

type 消息类型 = "user" | "agent" | "system" | "action" | "error";

interface 消息 {
  id: string;
  类型: 消息类型;
  内容: string;
  时间: Date;
}

interface 配置 {
  provider: "openai" | "gemini" | "anthropic";
  apiKey: string;
}

interface WSMessage {
  type: string;
  message: string | object; // message 可能是字符串或对象
}

// ============================================
// 主组件
// ============================================

export default function Home() {
  // 状态管理
  const [语言, set语言] = useState<语言类型>("zh");
  const t = 翻译[语言];

  const [消息列表, set消息列表] = useState<消息[]>([]);
  const [输入内容, set输入内容] = useState("");
  const [正在运行, set正在运行] = useState(false);
  const [已配置, set已配置] = useState(false);
  const [配置, set配置] = useState<配置>({ provider: "openai", apiKey: "" });
  const [配置对话框打开, set配置对话框打开] = useState(false);
  const [连接状态, set连接状态] = useState<"disconnected" | "connecting" | "connected">("disconnected");

  // 引用
  const 消息容器Ref = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // 后端 URL
  const API_BASE = "http://localhost:8000";
  const WS_URL = "ws://localhost:8000/ws";

  // ============================================
  // 消息管理
  // ============================================

  const 添加消息 = useCallback((类型: 消息类型, 内容: string) => {
    const 新消息: 消息 = {
      id: Date.now().toString() + Math.random().toString(36).slice(2),
      类型,
      内容,
      时间: new Date(),
    };
    set消息列表((prev) => [...prev, 新消息]);
  }, []);

  const 添加系统消息 = useCallback((内容: string) => 添加消息("system", 内容), [添加消息]);

  // ============================================
  // WebSocket 连接
  // ============================================

  // 创建 ref 来存储 WebSocket 连接函数
const 连接WebSocketRef = useRef<(() => void) | null>(null);

const 连接WebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    set连接状态("connecting");
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      set连接状态("connected");
      添加系统消息(t.msg_connected);
    };

    ws.onmessage = (event) => {
      try {
        const data: WSMessage = JSON.parse(event.data);

        // 处理特殊的 status 消息
        if (data.type === "status") {
          const statusData = data.message as { is_running: boolean };
          if (statusData.is_running === false) {
            set正在运行(false);
          }
          return;
        }

        const 类型映射: Record<string, 消息类型> = {
          info: "system",
          action: "action",
          error: "error",
        };

        // 确保 data.message 是字符串
        const content = typeof data.message === 'string' ? data.message : JSON.stringify(data.message);
        添加消息(类型映射[data.type] || "system", content);

      } catch {
        添加消息("system", event.data);
      }
    };

    ws.onclose = () => {
      set连接状态("disconnected");
      添加系统消息(t.msg_disconnected);
      // 使用 ref 来避免循环依赖
      setTimeout(() => {
        if (wsRef.current?.readyState !== WebSocket.OPEN && 连接WebSocketRef.current) {
          连接WebSocketRef.current();
        }
      }, 3000);
    };

    ws.onerror = () => {
      set连接状态("disconnected");
    };

    wsRef.current = ws;
  }, [t, 添加系统消息, 添加消息]); // 添加所有必要的依赖

  // 更新 ref
  useEffect(() => {
    连接WebSocketRef.current = 连接WebSocket;
  }, [连接WebSocket]);

  // 组件挂载时连接
  useEffect(() => {
    if (连接WebSocketRef.current) {
      连接WebSocketRef.current();
    }
    const heartbeat = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send("ping");
      }
    }, 30000);
    return () => {
      clearInterval(heartbeat);
      wsRef.current?.close();
    };
  }, []); // 只在组件挂载时运行一次

  useEffect(() => {
    消息容器Ref.current?.scrollTo({
      top: 消息容器Ref.current.scrollHeight,
      behavior: "smooth",
    });
  }, [消息列表]);

  // ============================================
  // API 调用
  // ============================================

  const 保存配置 = async () => {
    if (!配置.apiKey.trim()) {
      添加系统消息("❌ API Key Required");
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: 配置.provider,
          api_key: 配置.apiKey,
        }),
      });

      if (res.ok) {
        set已配置(true);
        set配置对话框打开(false);
        添加系统消息(`${t.msg_config_success} ${配置.provider.toUpperCase()}`);
      } else {
        const err = await res.json();
        添加系统消息(`${t.msg_config_fail}: ${err.detail}`);
      }
    } catch {
      添加系统消息("❌ Backend Error");
    }
  };

  const 发送任务 = async () => {
    if (!输入内容.trim()) return;
    if (!已配置) {
      添加系统消息(t.msg_config_first);
      return;
    }

    const 任务内容 = 输入内容.trim();
    set输入内容("");
    添加消息("user", 任务内容);

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: 任务内容 }),
      });

      if (res.ok) {
        set正在运行(true);
      } else {
        const err = await res.json();
        添加系统消息(`${t.msg_send_fail}: ${err.detail}`);
      }
    } catch {
      添加系统消息("❌ Backend Error");
    }
  };

  const 停止任务 = async () => {
    try {
      await fetch(`${API_BASE}/api/stop`, { method: "POST" });
      set正在运行(false);
      添加系统消息(t.msg_stop_sent);
    } catch {
      添加系统消息("❌ Failed to send stop signal");
    }
  };

  // ============================================
  // 渲染
  // ============================================

  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-br from-zinc-50 to-zinc-100 dark:from-zinc-900 dark:to-black transition-colors duration-500">
      {/* 顶部导航栏 */}
      <header className="sticky top-0 z-50 flex items-center justify-between border-b border-zinc-200/50 bg-white/80 px-6 py-4 backdrop-blur-xl dark:border-zinc-800/50 dark:bg-zinc-900/80">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 text-white shadow-lg shadow-violet-500/25">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M3 5a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2h-2.22l.123.489.804.804A1 1 0 0113 18H7a1 1 0 01-.707-1.707l.804-.804L7.22 15H5a2 2 0 01-2-2V5zm5.771 7H5V5h10v7H8.771z" clipRule="evenodd" />
            </svg>
          </div>
          <div>
            <h1 className="text-lg font-semibold text-zinc-900 dark:text-white">{t.title}</h1>
            <p className="text-xs text-zinc-500">{t.subtitle}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* 语言切换按钮 */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => set语言(语言 === "zh" ? "en" : "zh")}
            className="text-xs font-medium"
          >
            {t.lang_toggle}
          </Button>

          {/* 连接状态指示器 */}
          <div className="flex items-center gap-2 rounded-full bg-zinc-100 px-3 py-1.5 dark:bg-zinc-800">
            <div className={`h-2 w-2 rounded-full ${连接状态 === "connected" ? "bg-emerald-500 animate-pulse" :
                连接状态 === "connecting" ? "bg-amber-500 animate-pulse" :
                  "bg-zinc-400"
              }`} />
            <span className="text-xs font-medium text-zinc-600 dark:text-zinc-400">
              {连接状态 === "connected" ? t.status_connected : 连接状态 === "connecting" ? t.status_connecting : t.status_disconnected}
            </span>
          </div>

          {/* 设置按钮 */}
          <Dialog open={配置对话框打开} onOpenChange={set配置对话框打开}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm" className="gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                </svg>
                {已配置 ? t.config_btn_done : t.config_btn}
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle>{t.config_title}</DialogTitle>
                <DialogDescription>
                  {t.config_desc}
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="provider">{t.provider_label}</Label>
                  <Select
                    value={配置.provider}
                    onValueChange={(v) => set配置({ ...配置, provider: v as 配置["provider"] })}
                  >
                    <SelectTrigger id="provider">
                      <SelectValue placeholder={t.provider_placeholder} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="openai">OpenAI (GPT-4o)</SelectItem>
                      <SelectItem value="gemini">Google Gemini</SelectItem>
                      <SelectItem value="anthropic">Anthropic Claude</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="apiKey">{t.apikey_label}</Label>
                  <Input
                    id="apiKey"
                    type="password"
                    placeholder={t.apikey_placeholder}
                    value={配置.apiKey}
                    onChange={(e) => set配置({ ...配置, apiKey: e.target.value })}
                  />
                </div>
              </div>
              <div className="flex justify-end">
                <Button onClick={保存配置}>{t.save_btn}</Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </header>

      {/* 主要内容区 */}
      <main className="flex flex-1 flex-col items-center px-4 py-6">
        <Card className="flex h-[calc(100vh-180px)] w-full max-w-3xl flex-col overflow-hidden shadow-xl">
          <CardHeader className="border-b border-zinc-100 bg-zinc-50/50 dark:border-zinc-800 dark:bg-zinc-900/50">
            <CardTitle className="flex items-center justify-between text-base">
              <span>{t.chat_title}</span>
              {正在运行 && (
                <div className="flex items-center gap-2 text-sm font-normal text-amber-600">
                  <div className="h-2 w-2 animate-pulse rounded-full bg-amber-500" />
                  {t.agent_running}
                </div>
              )}
            </CardTitle>
          </CardHeader>

          <CardContent className="flex flex-1 flex-col gap-4 overflow-hidden p-0">
            {/* 消息列表 */}
            <div
              ref={消息容器Ref}
              className="flex-1 overflow-y-auto p-4"
            >
              {消息列表.length === 0 ? (
                <div className="flex h-full flex-col items-center justify-center text-center">
                  <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-100 to-purple-100 dark:from-violet-900/30 dark:to-purple-900/30">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-violet-600 dark:text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <h3 className="mb-2 text-lg font-medium text-zinc-900 dark:text-white">{t.welcome_title}</h3>
                  <p className="max-w-sm text-sm text-zinc-500 mb-4">
                    {t.welcome_desc}
                  </p>
                  <p className="text-xs text-zinc-400">
                    {t.devtools_tip}
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {消息列表.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex ${msg.类型 === "user" ? "justify-end" : "justify-start"}`}
                    >
                      <div
                        className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm ${msg.类型 === "user"
                            ? "bg-gradient-to-r from-violet-500 to-purple-600 text-white"
                            : msg.类型 === "error"
                              ? "bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400"
                              : msg.类型 === "action"
                                ? "bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
                                : "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
                          }`}
                      >
                        {msg.内容}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 输入区域 */}
            <div className="border-t border-zinc-100 p-4 dark:border-zinc-800">
              <div className="flex gap-2">
                <Textarea
                  placeholder={t.input_placeholder}
                  className="min-h-[60px] flex-1 resize-none"
                  value={输入内容}
                  onChange={(e) => set输入内容(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      发送任务();
                    }
                  }}
                  disabled={正在运行}
                />
                <div className="flex flex-col gap-2">
                  {正在运行 ? (
                    <Button
                      variant="destructive"
                      className="h-full"
                      onClick={停止任务}
                      title={t.stop_tooltip}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clipRule="evenodd" />
                      </svg>
                    </Button>
                  ) : (
                    <Button
                      className="h-full bg-gradient-to-r from-violet-500 to-purple-600 text-white hover:from-violet-600 hover:to-purple-700"
                      onClick={发送任务}
                      disabled={!输入内容.trim()}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
                      </svg>
                    </Button>
                  )}
                </div>
              </div>
              <p className="mt-2 text-center text-xs text-zinc-400">
                ⚠️ {t.stop_tooltip}
              </p>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
