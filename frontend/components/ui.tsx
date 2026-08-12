"use client";

import { ReactNode } from "react";
import { ChevronDown, ArrowUpRight, ArrowDownRight } from "lucide-react";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`bg-card border border-border rounded-xl p-5 ${className}`}>
      {children}
    </div>
  );
}

export function StatusPill({ online }: { online: boolean }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full ${
        online ? "bg-green/10 text-green" : "bg-red/10 text-red"
      }`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${online ? "bg-green" : "bg-red"}`} />
      {online ? "ONLINE" : "OFFLINE"}
    </span>
  );
}

export function Delta({ value, suffix = "% vs пред. неделя" }: { value: number; suffix?: string }) {
  const up = value >= 0;
  return (
    <span className={`inline-flex items-center gap-0.5 text-xs font-semibold ${up ? "text-green" : "text-red"}`}>
      {up ? <ArrowUpRight size={13} /> : <ArrowDownRight size={13} />}
      {up ? "+" : ""}
      {value}
      {suffix}
    </span>
  );
}

export function KpiCard({
  label,
  value,
  delta,
  unit,
}: {
  label: string;
  value: string | number;
  delta: number;
  unit?: string;
}) {
  return (
    <Card className="flex flex-col gap-2.5 min-w-0">
      <span className="text-[13px] text-textmuted font-medium">{label}</span>
      <span className="text-[28px] font-bold tracking-tight text-white">
        {value}
        {unit && <span className="text-[15px] text-textmuted font-medium"> {unit}</span>}
      </span>
      <Delta value={delta} />
    </Card>
  );
}

export function MiniStat({ label, value, colorClass = "text-white" }: { label: string; value: string | number; colorClass?: string }) {
  return (
    <div>
      <div className="text-[11px] text-textfaint mb-1">{label}</div>
      <div className={`text-[15px] font-semibold ${colorClass}`}>{value}</div>
    </div>
  );
}

export function Select({
  value,
  options,
  onChange,
  className = "w-[150px]",
}: {
  value: string;
  options: string[];
  onChange: (v: string) => void;
  className?: string;
}) {
  return (
    <div className={`relative ${className}`}>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full appearance-none bg-cardalt border border-border rounded-md text-white text-[13px] py-2 pl-3 pr-8 cursor-pointer"
      >
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
      <ChevronDown size={14} className="absolute right-2.5 top-2.5 text-textfaint pointer-events-none" />
    </div>
  );
}

export function SectionHeader({ title, subtitle, action }: { title: string; subtitle?: string; action?: ReactNode }) {
  return (
    <div className="flex items-start justify-between mb-3.5">
      <div>
        <div className="text-[14.5px] font-semibold text-white">{title}</div>
        {subtitle && <div className="text-xs text-textfaint mt-0.5">{subtitle}</div>}
      </div>
      {action}
    </div>
  );
}

export const inputClass =
  "w-full bg-bgsoft border border-border rounded-lg text-white text-[13px] px-3 py-2.5 outline-none focus:border-accent";
