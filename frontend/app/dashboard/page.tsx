"use client";

import { useEffect, useState, useCallback } from "react";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { AppShell } from "@/components/AppShell";
import { Topbar } from "@/components/Topbar";
import { LiveCamera } from "@/components/LiveCamera";
import { KpiCard, Card, SectionHeader } from "@/components/ui";
import { api } from "@/lib/api";
import { useWebSocket } from "@/lib/useWebSocket";

const WEEK_DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-cardalt border border-border rounded-lg px-3 py-2 text-xs">
      <div className="text-textmuted mb-1">{label}</div>
      {payload.map((p: any) => (
        <div key={p.dataKey} style={{ color: p.color }} className="font-semibold">
          {p.name}: {p.value}
        </div>
      ))}
    </div>
  );
}

export default function DashboardPage() {
  const [period, setPeriod] = useState("Сегодня");
  const [branch, setBranch] = useState("Все филиалы");
  const [cam, setCam] = useState("Все камеры");

  const [kpi, setKpi] = useState<any>(null);
  const [hourly, setHourly] = useState<any[]>([]);
  const [branches, setBranches] = useState<any[]>([]);
  const [alertsCount, setAlertsCount] = useState(0);
  const [camCounters, setCamCounters] = useState({ entries: 0, exits: 0 });

  const loadAll = useCallback(async () => {
    const [d, h, b, a] = await Promise.all([
      api.dashboard(), api.analyticsHourly(), api.branches(), api.alerts(),
    ]);
    setKpi(d);
    setHourly(h);
    setBranches(b);
    setAlertsCount(a.length);
    setCamCounters({ entries: d.entries, exits: d.exits });
  }, []);

  useEffect(() => { loadAll(); }, [loadAll]);

  // Живые ENTRY/EXIT события от backend (реальный AI-сервис или Demo Mode)
  useWebSocket("/ws/dashboard", (msg) => {
    if (msg.type !== "ENTRY" && msg.type !== "EXIT") return;
    setKpi((k: any) =>
      k
        ? {
            ...k,
            entries: msg.type === "ENTRY" ? k.entries + 1 : k.entries,
            exits: msg.type === "EXIT" ? k.exits + 1 : k.exits,
            visitors_today: msg.type === "ENTRY" ? k.visitors_today + 1 : k.visitors_today,
            current_inside: Math.max(0, k.current_inside + (msg.type === "ENTRY" ? 1 : -1)),
          }
        : k
    );
    setCamCounters((c) => ({
      entries: msg.type === "ENTRY" ? c.entries + 1 : c.entries,
      exits: msg.type === "EXIT" ? c.exits + 1 : c.exits,
    }));
  });

  // Дублируем событие и локально из симулированной камеры в UI (для наглядности
  // без реальных камер) — в проде эти события тоже приходят через тот же WS-канал.
  const handleLocalCamEvent = useCallback((type: "ENTRY" | "EXIT") => {
    setCamCounters((c) => ({
      entries: type === "ENTRY" ? c.entries + 1 : c.entries,
      exits: type === "EXIT" ? c.exits + 1 : c.exits,
    }));
  }, []);

  const weekData = WEEK_DAYS.map((d, i) => ({
    day: d,
    thisWeek: hourly.length ? hourly.reduce((s, h) => s + h.entries, 0) + i * 12 : 0,
    lastWeek: hourly.length ? hourly.reduce((s, h) => s + h.entries, 0) - 40 + i * 10 : 0,
  }));

  return (
    <AppShell>
      <Topbar
        period={period} setPeriod={setPeriod}
        branch={branch} setBranch={setBranch}
        cam={cam} setCam={setCam}
        branchOptions={["Все филиалы", ...branches.map((b) => b.name)]}
        alertsCount={alertsCount}
      />
      <div className="flex-1 overflow-y-auto px-7 py-5">
        {!kpi ? (
          <SkeletonDashboard />
        ) : (
          <div className="flex flex-col gap-5">
            <div className="grid grid-cols-6 gap-3.5">
              <KpiCard label="Посетителей сегодня" value={kpi.visitors_today.toLocaleString("ru-RU")} delta={kpi.deltas.visitors_today} />
              <KpiCard label="Входы" value={kpi.entries.toLocaleString("ru-RU")} delta={kpi.deltas.entries} />
              <KpiCard label="Выходы" value={kpi.exits.toLocaleString("ru-RU")} delta={kpi.deltas.exits} />
              <KpiCard label="Сейчас внутри" value={kpi.current_inside} delta={kpi.deltas.current_inside} />
              <KpiCard label="Среднее время" value={kpi.avg_dwell_minutes} unit="мин" delta={kpi.deltas.avg_dwell_minutes} />
              <KpiCard label="Конверсия" value={kpi.conversion_rate} unit="%" delta={kpi.deltas.conversion_rate} />
            </div>

            <LiveCamera entries={camCounters.entries} exits={camCounters.exits} onLocalEvent={handleLocalCamEvent} />

            <div className="grid grid-cols-[1.3fr_1fr] gap-3.5">
              <Card>
                <SectionHeader title="Посещаемость по часам" subtitle="Входы / выходы, текущий день" />
                <ResponsiveContainer width="100%" height={220}>
                  <AreaChart data={hourly}>
                    <defs>
                      <linearGradient id="gEntries" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#5B6EF5" stopOpacity={0.35} />
                        <stop offset="100%" stopColor="#5B6EF5" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="#1F2937" vertical={false} />
                    <XAxis dataKey="hour" tick={{ fill: "#6B7280", fontSize: 11 }} axisLine={{ stroke: "#1F2937" }} tickLine={false} />
                    <YAxis tick={{ fill: "#6B7280", fontSize: 11 }} axisLine={false} tickLine={false} width={28} />
                    <Tooltip content={<ChartTooltip />} />
                    <Area type="monotone" dataKey="entries" name="Входы" stroke="#5B6EF5" fill="url(#gEntries)" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </Card>

              <Card>
                <SectionHeader title="Сравнение недель" subtitle="Эта неделя vs прошлая" />
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={weekData}>
                    <CartesianGrid stroke="#1F2937" vertical={false} />
                    <XAxis dataKey="day" tick={{ fill: "#6B7280", fontSize: 11 }} axisLine={{ stroke: "#1F2937" }} tickLine={false} />
                    <YAxis tick={{ fill: "#6B7280", fontSize: 11 }} axisLine={false} tickLine={false} width={30} />
                    <Tooltip content={<ChartTooltip />} />
                    <Bar dataKey="lastWeek" name="Прошлая" fill="#1F2937" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="thisWeek" name="Эта неделя" fill="#5B6EF5" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}

function SkeletonDashboard() {
  return (
    <div className="grid grid-cols-6 gap-3.5">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="h-[110px] rounded-xl bg-card border border-border animate-pulse" />
      ))}
    </div>
  );
}
