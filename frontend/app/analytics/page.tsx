"use client";

import { useEffect, useState, useCallback } from "react";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { AppShell } from "@/components/AppShell";
import { Topbar } from "@/components/Topbar";
import { Card, SectionHeader } from "@/components/ui";
import { api } from "@/lib/api";

function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-cardalt border border-border rounded-lg px-3 py-2 text-xs">
      <div className="text-textmuted mb-1">{label}</div>
      {payload.map((p: any) => (
        <div key={p.dataKey} style={{ color: p.color }} className="font-semibold">{p.name}: {p.value}</div>
      ))}
    </div>
  );
}

export default function AnalyticsPage() {
  const [period, setPeriod] = useState("7 дней");
  const [branch, setBranch] = useState("Все филиалы");
  const [cam, setCam] = useState("Все камеры");

  const [hourly, setHourly] = useState<any[]>([]);
  const [branches, setBranches] = useState<any[]>([]);
  const [heatmap, setHeatmap] = useState<any[]>([]);

  const load = useCallback(async () => {
    const [h, b, hm] = await Promise.all([api.analyticsHourly(), api.branches(), api.analyticsHeatmap()]);
    setHourly(h);
    setBranches(b);
    setHeatmap(hm);
  }, []);
  useEffect(() => { load(); }, [load]);

  const zones = Array.from(new Set(heatmap.map((c) => c.zone)));
  const slots = Array.from(new Set(heatmap.map((c) => c.slot)));
  const maxHeat = Math.max(1, ...heatmap.map((c) => c.value));

  return (
    <AppShell>
      <Topbar
        period={period} setPeriod={setPeriod} branch={branch} setBranch={setBranch} cam={cam} setCam={setCam}
        branchOptions={["Все филиалы", ...branches.map((b) => b.name)]}
      />
      <div className="flex-1 overflow-y-auto px-7 py-5 flex flex-col gap-4">
        <div className="text-base font-semibold text-white">Аналитика</div>

        <div className="grid grid-cols-2 gap-3.5">
          <Card>
            <SectionHeader title="Входы / выходы" subtitle="По часам, текущий день" />
            <ResponsiveContainer width="100%" height={210}>
              <LineChart data={hourly}>
                <CartesianGrid stroke="#1F2937" vertical={false} />
                <XAxis dataKey="hour" tick={{ fill: "#6B7280", fontSize: 11 }} axisLine={{ stroke: "#1F2937" }} tickLine={false} />
                <YAxis tick={{ fill: "#6B7280", fontSize: 11 }} axisLine={false} tickLine={false} width={28} />
                <Tooltip content={<ChartTooltip />} />
                <Line type="monotone" dataKey="entries" name="Входы" stroke="#22C55E" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="exits" name="Выходы" stroke="#EF4444" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </Card>

          <Card>
            <SectionHeader title="Сравнение филиалов" subtitle="Посетители сегодня" />
            <ResponsiveContainer width="100%" height={210}>
              <BarChart data={branches} layout="vertical" margin={{ left: 10 }}>
                <CartesianGrid stroke="#1F2937" horizontal={false} />
                <XAxis type="number" tick={{ fill: "#6B7280", fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="name" tick={{ fill: "#9CA3AF", fontSize: 11.5 }} axisLine={false} tickLine={false} width={95} />
                <Tooltip content={<ChartTooltip />} />
                <Bar dataKey="visitors_today" name="Посетители" fill="#5B6EF5" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </div>

        <Card>
          <SectionHeader title="Пиковые часы" subtitle="Наибольшая посещаемость" />
          <div className="flex gap-2.5">
            <span className="bg-accent/10 text-accent text-xs font-semibold px-3 py-1.5 rounded-full">12:00 – 14:00</span>
            <span className="bg-accent/10 text-accent text-xs font-semibold px-3 py-1.5 rounded-full">18:00 – 20:00</span>
          </div>
        </Card>

        <Card>
          <SectionHeader title="Тепловая карта" subtitle="Плотность посетителей по зонам магазина" />
          <div className="grid gap-1.5 items-center" style={{ gridTemplateColumns: `110px repeat(${slots.length || 1}, 1fr)` }}>
            <div />
            {slots.map((s) => <div key={s} className="text-[11px] text-textfaint text-center">{s}</div>)}
            {zones.map((zone) => (
              <div key={zone} className="contents">
                <div className="text-[12.5px] text-textmuted">{zone}</div>
                {slots.map((slot) => {
                  const cell = heatmap.find((c) => c.zone === zone && c.slot === slot);
                  const value = cell?.value || 0;
                  const alpha = 0.08 + (value / maxHeat) * 0.75;
                  return (
                    <div
                      key={slot}
                      className="h-[34px] rounded flex items-center justify-center text-[11px] font-semibold"
                      style={{ background: `rgba(91,110,245,${alpha})`, color: alpha > 0.5 ? "#fff" : "#9CA3AF" }}
                    >
                      {value}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
