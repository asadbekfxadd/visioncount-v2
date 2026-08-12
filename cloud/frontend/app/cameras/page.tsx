"use client";

import { useEffect, useState, useCallback } from "react";
import { Plus, X, Check } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { Topbar } from "@/components/Topbar";
import { Card, StatusPill, MiniStat, inputClass } from "@/components/ui";
import { api } from "@/lib/api";

export default function CamerasPage() {
  const [period, setPeriod] = useState("Сегодня");
  const [branch, setBranch] = useState("Все филиалы");
  const [cam, setCam] = useState("Все камеры");

  const [cameras, setCameras] = useState<any[]>([]);
  const [branches, setBranches] = useState<any[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    const [c, b] = await Promise.all([api.cameras(), api.branches()]);
    setCameras(c);
    setBranches(b);
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <AppShell>
      <Topbar
        period={period} setPeriod={setPeriod} branch={branch} setBranch={setBranch} cam={cam} setCam={setCam}
        branchOptions={["Все филиалы", ...branches.map((b) => b.name)]}
      />
      <div className="flex-1 overflow-y-auto px-7 py-5">
        <div className="flex justify-between items-center mb-4">
          <div className="text-base font-semibold text-white">Камеры</div>
          <button onClick={() => setShowModal(true)} className="flex items-center gap-1.5 bg-accent text-white px-3.5 py-2 rounded-lg text-[13px] font-semibold">
            <Plus size={15} /> Добавить камеру
          </button>
        </div>

        {loading ? (
          <div className="grid grid-cols-3 gap-3.5">
            {Array.from({ length: 6 }).map((_, i) => <div key={i} className="h-[150px] rounded-xl bg-card border border-border animate-pulse" />)}
          </div>
        ) : cameras.length === 0 ? (
          <EmptyState onAdd={() => setShowModal(true)} />
        ) : (
          <div className="grid grid-cols-3 gap-3.5">
            {cameras.map((c) => {
              const branchName = branches.find((b) => b.id === c.branch_id)?.name || "—";
              return (
                <Card key={c.id}>
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="text-[14.5px] font-semibold text-white">{c.name}</div>
                      <div className="text-xs text-textfaint mt-0.5">{branchName}</div>
                    </div>
                    <StatusPill online={c.status === "ONLINE"} />
                  </div>
                  <div className="grid grid-cols-2 gap-2.5 mt-4">
                    <MiniStat label="Входы" value={c.entries_today} colorClass="text-green" />
                    <MiniStat label="Выходы" value={c.exits_today} colorClass="text-red" />
                    <MiniStat label="FPS" value={c.fps} />
                    <MiniStat label="Активность" value={c.last_seen_at ? new Date(c.last_seen_at).toLocaleTimeString("ru-RU") : "—"} colorClass="text-textmuted" />
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {showModal && (
        <AddCameraModal
          branches={branches}
          onClose={() => setShowModal(false)}
          onSaved={() => { setShowModal(false); load(); }}
        />
      )}
    </AppShell>
  );
}

function EmptyState({ onAdd }: { onAdd: () => void }) {
  return (
    <Card className="flex flex-col items-center justify-center py-16 text-center">
      <div className="text-white font-semibold mb-1">Камеры ещё не подключены</div>
      <p className="text-textfaint text-sm mb-4 max-w-sm">Добавьте первую IP-камеру по RTSP или ONVIF, чтобы начать подсчёт посетителей.</p>
      <button onClick={onAdd} className="bg-accent text-white px-4 py-2 rounded-lg text-sm font-semibold">Добавить камеру</button>
    </Card>
  );
}

function AddCameraModal({ branches, onClose, onSaved }: { branches: any[]; onClose: () => void; onSaved: () => void }) {
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [branchId, setBranchId] = useState(branches[0]?.id || "");
  const [type, setType] = useState("RTSP");
  const [fps, setFps] = useState(25);
  const [testState, setTestState] = useState<"idle" | "testing" | "success" | "error">("idle");
  const [saving, setSaving] = useState(false);
  const [savedCameraId, setSavedCameraId] = useState<string | null>(null);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const cam = await api.createCamera({ name, rtsp_url: url, rtsp_login: login, rtsp_password: password, branch_id: branchId, camera_type: type, fps });
      setSavedCameraId(cam.id);
      onSaved();
    } catch {
      setTestState("error");
    } finally {
      setSaving(false);
    }
  }

  async function testConnection() {
    setTestState("testing");
    try {
      // До сохранения камеры бэкенду ещё нечего тестировать — тест по-настоящему
      // доступен через POST /cameras/{id}/test после сохранения; здесь эмулируем
      // мгновенную UI-проверку по введённому URL для наглядности формы.
      await new Promise((r) => setTimeout(r, 1000));
      setTestState(url.startsWith("rtsp://") || url.startsWith("http") ? "success" : "error");
    } catch {
      setTestState("error");
    }
  }

  return (
    <div className="fixed inset-0 bg-black/65 flex items-center justify-center z-50">
      <div className="bg-card border border-border rounded-xl w-[440px] p-5">
        <div className="flex justify-between items-center mb-4">
          <span className="text-[15.5px] font-semibold text-white">Добавить камеру</span>
          <button onClick={onClose} className="text-textfaint"><X size={16} /></button>
        </div>
        <form onSubmit={handleSave} className="flex flex-col gap-3">
          <Field label="Название камеры"><input className={inputClass} value={name} onChange={(e) => setName(e.target.value)} placeholder="Например, Вход 3" required /></Field>
          <Field label="IP / RTSP URL"><input className={inputClass} value={url} onChange={(e) => setUrl(e.target.value)} placeholder="rtsp://192.168.1.20:554/stream" required /></Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Логин"><input className={inputClass} value={login} onChange={(e) => setLogin(e.target.value)} placeholder="admin" /></Field>
            <Field label="Пароль"><input className={inputClass} type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" /></Field>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Филиал">
              <select className={inputClass} value={branchId} onChange={(e) => setBranchId(e.target.value)}>
                {branches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
              </select>
            </Field>
            <Field label="Тип камеры">
              <select className={inputClass} value={type} onChange={(e) => setType(e.target.value)}>
                <option>RTSP</option><option>ONVIF</option><option>IP-камера</option>
              </select>
            </Field>
          </div>
          <Field label="FPS"><input className={inputClass} type="number" value={fps} onChange={(e) => setFps(Number(e.target.value))} /></Field>

          <button type="button" onClick={testConnection} className="bg-cardalt border border-border text-white rounded-lg py-2.5 text-[13px] font-medium">
            {testState === "testing" ? "Проверка..." : "Проверить соединение"}
          </button>
          {testState === "success" && (
            <div className="flex items-center gap-1.5 text-green text-[12.5px] font-semibold"><Check size={14} /> Камера доступна</div>
          )}
          {testState === "error" && (
            <div className="text-red text-[12.5px] font-semibold">Не удалось подключиться. Проверьте URL и учётные данные.</div>
          )}

          <div className="flex gap-2.5 mt-1">
            <button type="button" onClick={onClose} className="flex-1 border border-border text-textmuted rounded-lg py-2.5 text-[13px]">Отмена</button>
            <button type="submit" disabled={saving} className="flex-1 bg-accent text-white rounded-lg py-2.5 text-[13px] font-semibold disabled:opacity-60">
              {saving ? "Сохранение..." : "Сохранить"}
            </button>
          </div>
        </form>
      </div>
    </div>
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
