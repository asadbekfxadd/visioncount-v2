"use client";

import { useEffect, useState, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/api";
import { Sidebar } from "./Sidebar";

/**
 * Общий каркас для всех защищённых страниц: проверяет наличие JWT в
 * localStorage (иначе редиректит на /login) и рендерит боковую панель.
 */
export function AppShell({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    setReady(true);
  }, [router]);

  if (!ready) {
    return (
      <div className="h-screen w-full bg-bg flex items-center justify-center text-textmuted text-sm">
        Загрузка…
      </div>
    );
  }

  return (
    <div className="flex h-screen w-full bg-bg text-white overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">{children}</div>
    </div>
  );
}
