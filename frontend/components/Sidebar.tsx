"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard, Camera, Building2, BarChart3, FileText, Bell,
  Users, Settings, ChevronDown, User, Eye, Building, LogOut,
} from "lucide-react";
import { clearSession, getUser } from "@/lib/api";

const NAV = [
  { href: "/dashboard", label: "Дашборд", icon: LayoutDashboard },
  { href: "/cameras", label: "Камеры", icon: Camera },
  { href: "/branches", label: "Филиалы", icon: Building2 },
  { href: "/analytics", label: "Аналитика", icon: BarChart3 },
  { href: "/reports", label: "Отчёты", icon: FileText },
  { href: "/notifications", label: "Уведомления", icon: Bell },
  { href: "/users", label: "Пользователи", icon: Users },
  { href: "/settings", label: "Настройки", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const user = getUser<{ full_name: string; role: string }>();

  return (
    <div className="w-[236px] min-w-[236px] bg-bgsoft border-r border-border flex flex-col h-screen">
      <div className="px-5 pt-6 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-[30px] h-[30px] rounded-lg bg-accent flex items-center justify-center">
            <Eye size={16} color="#fff" />
          </div>
          <span className="text-[17px] font-bold tracking-tight text-white">VisionCount</span>
        </div>
        <div className="text-[11.5px] text-textfaint mt-1.5 ml-0.5">People Analytics</div>
      </div>

      <div className="flex-1 px-3 py-1.5 flex flex-col gap-0.5">
        {NAV.map((item) => {
          const Icon = item.icon;
          const active = pathname?.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-[13.5px] transition-colors ${
                active ? "bg-accent/10 text-accent font-semibold" : "text-textmuted font-medium hover:bg-cardalt"
              }`}
            >
              <Icon size={16} />
              {item.label}
            </Link>
          );
        })}
      </div>

      <div className="p-3.5 border-t border-border flex flex-col gap-2.5">
        <div className="flex items-center gap-2 bg-cardalt border border-border rounded-lg px-2.5 py-2">
          <Building size={14} className="text-textmuted" />
          <span className="text-xs text-white flex-1 truncate">VisionCount Retail</span>
          <ChevronDown size={13} className="text-textfaint" />
        </div>
        <div className="flex items-center gap-2.5 px-1">
          <div className="w-8 h-8 rounded-full bg-accent/10 flex items-center justify-center text-accent">
            <User size={15} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs font-semibold text-white truncate">{user?.full_name || "Пользователь"}</div>
            <div className="text-[11px] text-textfaint">{user?.role || "VIEWER"}</div>
          </div>
          <button
            title="Выйти"
            onClick={() => {
              clearSession();
              router.push("/login");
            }}
            className="text-textfaint hover:text-red"
          >
            <LogOut size={15} />
          </button>
        </div>
      </div>
    </div>
  );
}
