"use client";

import { useState } from "react";
import { ShieldCheck } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { Topbar } from "@/components/Topbar";
import { Card, SectionHeader, inputClass } from "@/components/ui";

export default function SettingsPage() {
  const [period, setPeriod] = useState("Сегодня");
  const [branch, setBranch] = useState("Все филиалы");
  const [cam, setCam] = useState("Все камеры");

  return (
    <AppShell>
      <Topbar period={period} setPeriod={setPeriod} branch={branch} setBranch={setBranch} cam={cam} setCam={setCam} />
      <div className="flex-1 overflow-y-auto px-7 py-5">
        <div className="text-base font-semibold text-white mb-4">Настройки</div>
        <div className="max-w-[560px] flex flex-col gap-4">
          <Card>
            <SectionHeader title="Компания" />
            <div className="flex flex-col gap-3">
              <Field label="Название компании"><input className={inputClass} defaultValue="VisionCount Retail" /></Field>
              <Field label="Часовой пояс"><input className={inputClass} defaultValue="Asia/Tashkent (UTC+5)" /></Field>
            </div>
          </Card>
          <Card>
            <SectionHeader title="Пороги уведомлений" />
            <div className="flex flex-col gap-3">
              <Field label="Лимит посетителей одновременно"><input className={inputClass} type="number" defaultValue={200} /></Field>
              <Field label="Порог аномального падения (%)"><input className={inputClass} type="number" defaultValue={30} /></Field>
            </div>
          </Card>
          <div className="flex items-center gap-2 text-textfaint text-xs">
            <ShieldCheck size={14} /> Пароли камер хранятся зашифрованными и не передаются на клиент.
          </div>
        </div>
      </div>
    </AppShell>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1.5 text-[12.5px] text-textmuted">
      {label}
      {children}
    </label>
  );
}
