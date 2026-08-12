"use client";

import { useEffect, useState, useCallback } from "react";
import { AlertTriangle, Check, Clock } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { Topbar } from "@/components/Topbar";
import { Card } from "@/components/ui";
import { api } from "@/lib/api";

const TYPE_STYLE: Record<string, { color: string; bg: string }> = {
  CAMERA_OFFLINE: { color: "text-red", bg: "bg-red/10" },
  LIMIT_EXCEEDED: { color: "text-amber", bg: "bg-amber/10" },
  ANOMALY_DROP: { color: "text-amber", bg: "bg-amber/10" },
};

export default function NotificationsPage() {
  const [period, setPeriod] = useState("Сегодня");
  const [branch, setBranch] = useState("Все филиалы");
  const [cam, setCam] = useState("Все камеры");
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setAlerts(await api.alerts());
    setLoading(false);
  }, []);
  useEffect(() => { load(); }, [load]);

  return (
    <AppShell>
      <Topbar period={period} setPeriod={setPeriod} branch={branch} setBranch={setBranch} cam={cam} setCam={setCam} />
      <div className="flex-1 overflow-y-auto px-7 py-5">
        <div className="text-base font-semibold text-white mb-4">Уведомления</div>
        {loading ? (
          <div className="flex flex-col gap-2.5">
            {Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-16 rounded-xl bg-card border border-border animate-pulse" />)}
          </div>
        ) : alerts.length === 0 ? (
          <Card className="text-center py-14 text-textfaint text-sm">Активных уведомлений нет — всё работает штатно.</Card>
        ) : (
          <div className="flex flex-col gap-2.5">
            {alerts.map((a) => {
              const style = TYPE_STYLE[a.type] || { color: "text-green", bg: "bg-green/10" };
              return (
                <Card key={a.id} className="flex gap-3 items-start">
                  <div className={`w-8 h-8 min-w-[32px] rounded-lg flex items-center justify-center ${style.bg} ${style.color}`}>
                    <AlertTriangle size={16} />
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between">
                      <span className="text-[13.5px] font-semibold text-white">{a.title}</span>
                      <span className="text-[11.5px] text-textfaint flex items-center gap-1">
                        <Clock size={11} /> {new Date(a.created_at).toLocaleString("ru-RU")}
                      </span>
                    </div>
                    <div className="text-[12.5px] text-textmuted mt-0.5">{a.message}</div>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </AppShell>
  );
}
