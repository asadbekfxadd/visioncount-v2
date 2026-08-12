"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { Pause, Play, Aperture, Settings, Maximize2, Minimize2 } from "lucide-react";
import { Card, StatusPill } from "./ui";

type Person = { id: number; x: number; lane: number; speed: number; entered: boolean; exited: boolean };

/**
 * Визуализация "живой" камеры для Demo Mode: синтетические люди пересекают
 * зелёную линию ВХОД (30%) и красную линию ВЫХОД (70%), эмулируя ровно тот
 * же поток событий, что реальный pipeline YOLO -> tracker -> line crossing
 * шлёт через POST /internal/events -> WebSocket.
 */
export function LiveCamera({
  cameraName = "Вход 1",
  entries,
  exits,
  onLocalEvent,
}: {
  cameraName?: string;
  entries: number;
  exits: number;
  onLocalEvent: (type: "ENTRY" | "EXIT") => void;
}) {
  const [people, setPeople] = useState<Person[]>([]);
  const [paused, setPaused] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const nextId = useRef(1);
  const laneCount = 4;
  const height = expanded ? 460 : 300;

  const handleEvent = useCallback((t: "ENTRY" | "EXIT") => onLocalEvent(t), [onLocalEvent]);

  useEffect(() => {
    if (paused) return;
    const spawn = setInterval(() => {
      setPeople((prev) => {
        if (prev.length > 7) return prev;
        return [...prev, { id: nextId.current++, x: -6, lane: Math.floor(Math.random() * laneCount), speed: 0.55 + Math.random() * 0.5, entered: false, exited: false }];
      });
    }, 1500);

    const move = setInterval(() => {
      setPeople((prev) => {
        const next: Person[] = [];
        for (const p of prev) {
          const nx = p.x + p.speed;
          let entered = p.entered;
          let exited = p.exited;
          if (!entered && nx >= 30) { entered = true; handleEvent("ENTRY"); }
          if (entered && !exited && nx >= 70) { exited = true; handleEvent("EXIT"); }
          if (nx < 106) next.push({ ...p, x: nx, entered, exited });
        }
        return next;
      });
    }, 110);

    return () => { clearInterval(spawn); clearInterval(move); };
  }, [paused, handleEvent]);

  return (
    <Card className="p-0 overflow-hidden">
      <div className="flex items-center justify-between px-5 pt-4 pb-3">
        <div className="flex items-center gap-3">
          <span className="text-[15.5px] font-semibold text-white">Камера: {cameraName}</span>
          <StatusPill online />
        </div>
        <div className="flex gap-2">
          <IconButton icon={paused ? Play : Pause} onClick={() => setPaused((p) => !p)} title={paused ? "Возобновить" : "Пауза"} />
          <IconButton icon={Aperture} title="Скриншот" />
          <IconButton icon={Settings} title="Настройки камеры" />
          <IconButton icon={expanded ? Minimize2 : Maximize2} onClick={() => setExpanded((e) => !e)} title="Полноэкранный режим" />
        </div>
      </div>

      <div
        className="relative mx-5 mb-4 rounded-lg overflow-hidden border"
        style={{
          height,
          background: "linear-gradient(180deg,#0C1220 0%,#0A0E18 60%,#080B12 100%)",
          borderColor: "#182131",
        }}
      >
        <div
          className="absolute inset-0"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.035) 1px, transparent 1px)",
            backgroundSize: "34px 34px",
          }}
        />

        <div className="absolute top-0 bottom-0 w-0.5 bg-green/85" style={{ left: "30%" }} />
        <div className="absolute bg-green/10 text-green text-[11px] font-bold px-2 py-0.5 rounded-full" style={{ left: "30%", top: 10, transform: "translateX(-50%)" }}>
          ВХОД
        </div>

        <div className="absolute top-0 bottom-0 w-0.5 bg-red/85" style={{ left: "70%" }} />
        <div className="absolute bg-red/10 text-red text-[11px] font-bold px-2 py-0.5 rounded-full" style={{ left: "70%", top: 10, transform: "translateX(-50%)" }}>
          ВЫХОД
        </div>

        {people.map((p) => (
          <div key={p.id} className="absolute" style={{ left: `${p.x}%`, top: 18 + (p.lane * (height - 90)) / laneCount, transition: "left 0.1s linear" }}>
            <div className="text-[10px] text-accent font-bold mb-0.5 text-center">ID:{p.id}</div>
            <div
              className="w-[26px] h-[36px] rounded"
              style={{
                border: `2px solid ${p.exited ? "#EF4444" : p.entered ? "#5B6EF5" : "#22C55E"}`,
                background: "rgba(91,110,245,0.08)",
              }}
            />
          </div>
        ))}

        <div className="absolute left-3.5 bottom-3 flex items-center gap-2">
          <span className="w-[7px] h-[7px] rounded-full bg-red" />
          <span className="text-[11.5px] font-bold text-white tracking-widest">LIVE</span>
        </div>

        <div className="absolute right-3.5 bottom-3 flex gap-2.5">
          <div className="bg-green/15 border border-green/40 rounded-lg px-2.5 py-1 text-xs text-green font-bold">ВХОД {entries}</div>
          <div className="bg-red/15 border border-red/40 rounded-lg px-2.5 py-1 text-xs text-red font-bold">ВЫХОД {exits}</div>
        </div>
      </div>
    </Card>
  );
}

function IconButton({ icon: Icon, onClick, title }: { icon: any; onClick?: () => void; title: string }) {
  return (
    <button onClick={onClick} title={title} className="w-8 h-8 rounded-lg flex items-center justify-center border border-border text-textmuted hover:text-white hover:border-accent/50">
      <Icon size={15} />
    </button>
  );
}
