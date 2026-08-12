"use client";

import { useEffect, useState, useCallback } from "react";
import { FileText, Download } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { Topbar } from "@/components/Topbar";
import { Card } from "@/components/ui";
import { api } from "@/lib/api";

const REPORT_TYPES = [
  { type: "attendance", title: "Отчёт по посещаемости", desc: "Общая динамика входов и выходов за период" },
  { type: "branches", title: "Отчёт по филиалам", desc: "Сравнение показателей всех точек" },
  { type: "cameras", title: "Отчёт по камерам", desc: "Статус, FPS и активность каждой камеры" },
  { type: "hourly", title: "Отчёт по часам", desc: "Распределение посетителей по часам дня" },
  { type: "comparison", title: "Сравнение периодов", desc: "Текущий период относительно предыдущего" },
];

export default function ReportsPage() {
  const [period, setPeriod] = useState("7 дней");
  const [branch, setBranch] = useState("Все филиалы");
  const [cam, setCam] = useState("Все камеры");
  const [reports, setReports] = useState<any[]>([]);
  const [toast, setToast] = useState<string | null>(null);

  const load = useCallback(async () => setReports(await api.reports()), []);
  useEffect(() => { load(); }, [load]);

  async function handleExport(type: string, title: string, format: string) {
    const now = new Date();
    const start = new Date(now.getTime() - 7 * 24 * 3600 * 1000);
    await api.createReport({ type, format, period_start: start.toISOString(), period_end: now.toISOString() });
    setToast(`${title} — экспорт в ${format} запущен`);
    load();
    setTimeout(() => setToast(null), 4000);
  }

  return (
    <AppShell>
      <Topbar period={period} setPeriod={setPeriod} branch={branch} setBranch={setBranch} cam={cam} setCam={setCam} />
      <div className="flex-1 overflow-y-auto px-7 py-5">
        <div className="text-base font-semibold text-white mb-4">Отчёты</div>
        <div className="flex flex-col gap-2.5">
          {REPORT_TYPES.map((r) => (
            <Card key={r.type} className="flex items-center justify-between">
              <div className="flex gap-3 items-center">
                <div className="w-9 h-9 rounded-lg bg-accent/10 flex items-center justify-center text-accent">
                  <FileText size={16} />
                </div>
                <div>
                  <div className="text-[13.5px] font-semibold text-white">{r.title}</div>
                  <div className="text-xs text-textfaint">{r.desc}</div>
                </div>
              </div>
              <div className="flex gap-2">
                {["CSV", "Excel", "PDF"].map((f) => (
                  <button key={f} onClick={() => handleExport(r.type, r.title, f)} className="flex items-center gap-1.5 bg-cardalt border border-border text-textmuted text-xs px-2.5 py-1.5 rounded-lg hover:text-white">
                    <Download size={12} /> {f}
                  </button>
                ))}
              </div>
            </Card>
          ))}
        </div>

        {reports.length > 0 && (
          <div className="mt-6">
            <div className="text-sm font-semibold text-white mb-2.5">История экспортов</div>
            <Card className="p-0">
              {reports.map((r, i) => (
                <div key={r.id} className={`flex items-center justify-between px-4 py-3 ${i < reports.length - 1 ? "border-b border-border" : ""}`}>
                  <span className="text-[13px] text-white">{r.type}</span>
                  <span className="text-xs text-textfaint">{r.format} · {new Date(r.created_at).toLocaleString("ru-RU")}</span>
                </div>
              ))}
            </Card>
          </div>
        )}
      </div>

      {toast && (
        <div className="fixed bottom-5 right-5 bg-cardalt border border-border rounded-xl px-4 py-3 text-sm text-white shadow-xl">
          {toast}
        </div>
      )}
    </AppShell>
  );
}
