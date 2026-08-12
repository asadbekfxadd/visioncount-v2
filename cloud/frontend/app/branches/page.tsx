"use client";

import { useEffect, useState, useCallback } from "react";
import { ChevronRight } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { Topbar } from "@/components/Topbar";
import { Card, MiniStat } from "@/components/ui";
import { api } from "@/lib/api";

export default function BranchesPage() {
  const [period, setPeriod] = useState("Сегодня");
  const [branch, setBranch] = useState("Все филиалы");
  const [cam, setCam] = useState("Все камеры");
  const [branches, setBranches] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setBranches(await api.branches());
    setLoading(false);
  }, []);
  useEffect(() => { load(); }, [load]);

  return (
    <AppShell>
      <Topbar period={period} setPeriod={setPeriod} branch={branch} setBranch={setBranch} cam={cam} setCam={setCam} />
      <div className="flex-1 overflow-y-auto px-7 py-5">
        <div className="text-base font-semibold text-white mb-4">Филиалы</div>
        {loading ? (
          <div className="grid grid-cols-2 gap-3.5">
            {Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-[170px] rounded-xl bg-card border border-border animate-pulse" />)}
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-3.5">
            {branches.map((b) => (
              <Card key={b.id} className="cursor-pointer">
                <div className="flex justify-between items-center">
                  <div className="text-[15px] font-semibold text-white">{b.name}</div>
                  <ChevronRight size={16} className="text-textfaint" />
                </div>
                <div className="text-xs text-textfaint mt-0.5">{b.camera_count} камеры · {b.cameras_online} онлайн</div>
                <div className="grid grid-cols-4 gap-3 mt-4">
                  <MiniStat label="Сегодня" value={b.visitors_today.toLocaleString("ru-RU")} />
                  <MiniStat label="Входы" value={b.entries_today.toLocaleString("ru-RU")} colorClass="text-green" />
                  <MiniStat label="Выходы" value={b.exits_today.toLocaleString("ru-RU")} colorClass="text-red" />
                  <MiniStat label="Внутри" value={b.current_occupancy} colorClass="text-accent" />
                </div>
                <div className="mt-3 text-xs text-textfaint">
                  Среднее время пребывания: <span className="text-white font-semibold">{b.avg_dwell_minutes} мин</span>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
