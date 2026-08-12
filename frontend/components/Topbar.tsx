"use client";

import { useRouter } from "next/navigation";
import { Bell, User } from "lucide-react";
import { Select } from "./ui";

export function Topbar({
  period, setPeriod, branch, setBranch, cam, setCam,
  branchOptions = ["Все филиалы"], camOptions = ["Все камеры"],
  alertsCount = 0,
}: {
  period: string; setPeriod: (v: string) => void;
  branch: string; setBranch: (v: string) => void;
  cam: string; setCam: (v: string) => void;
  branchOptions?: string[]; camOptions?: string[];
  alertsCount?: number;
}) {
  const router = useRouter();
  return (
    <div className="flex items-center justify-between px-7 py-4 border-b border-border">
      <div className="flex gap-2.5">
        <Select value={period} options={["Сегодня", "7 дней", "30 дней", "3 месяца"]} onChange={setPeriod} className="w-[130px]" />
        <Select value={branch} options={branchOptions} onChange={setBranch} className="w-[170px]" />
        <Select value={cam} options={camOptions} onChange={setCam} className="w-[150px]" />
      </div>
      <div className="flex items-center gap-3.5">
        <button onClick={() => router.push("/notifications")} className="relative text-textmuted">
          <Bell size={18} />
          {alertsCount > 0 && (
            <span className="absolute -top-1 -right-1 w-[15px] h-[15px] rounded-full bg-red text-white text-[9px] font-bold flex items-center justify-center">
              {alertsCount}
            </span>
          )}
        </button>
        <div className="w-[30px] h-[30px] rounded-full bg-accent/10 flex items-center justify-center text-accent">
          <User size={15} />
        </div>
      </div>
    </div>
  );
}
