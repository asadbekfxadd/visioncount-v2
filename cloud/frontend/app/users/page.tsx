"use client";

import { useEffect, useState, useCallback } from "react";
import { Plus, MoreVertical, X } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { Topbar } from "@/components/Topbar";
import { Card, inputClass } from "@/components/ui";
import { api } from "@/lib/api";

const ROLE_COLOR: Record<string, string> = {
  OWNER: "text-accent bg-accent/15",
  ADMIN: "text-green bg-green/15",
  MANAGER: "text-amber bg-amber/15",
  ANALYST: "text-purple-400 bg-purple-400/15",
  VIEWER: "text-textmuted bg-white/10",
};

export default function UsersPage() {
  const [period, setPeriod] = useState("Сегодня");
  const [branch, setBranch] = useState("Все филиалы");
  const [cam, setCam] = useState("Все камеры");
  const [users, setUsers] = useState<any[]>([]);
  const [showModal, setShowModal] = useState(false);

  const load = useCallback(async () => setUsers(await api.users()), []);
  useEffect(() => { load(); }, [load]);

  return (
    <AppShell>
      <Topbar period={period} setPeriod={setPeriod} branch={branch} setBranch={setBranch} cam={cam} setCam={setCam} />
      <div className="flex-1 overflow-y-auto px-7 py-5">
        <div className="flex justify-between items-center mb-4">
          <div className="text-base font-semibold text-white">Пользователи</div>
          <button onClick={() => setShowModal(true)} className="flex items-center gap-1.5 bg-accent text-white px-3.5 py-2 rounded-lg text-[13px] font-semibold">
            <Plus size={15} /> Пригласить
          </button>
        </div>

        <Card className="p-0">
          {users.map((u, i) => (
            <div key={u.id} className={`flex items-center gap-3 px-4 py-3.5 ${i < users.length - 1 ? "border-b border-border" : ""}`}>
              <div className="rounded-full bg-accent/10 flex items-center justify-center text-accent text-xs font-bold" style={{ width: 34, height: 34 }}>
                {u.full_name.split(" ").map((p: string) => p[0]).join("")}
              </div>
              <div className="flex-1">
                <div className="text-[13.5px] font-semibold text-white">{u.full_name}</div>
                <div className="text-xs text-textfaint">{u.email}</div>
              </div>
              <span className={`text-[11.5px] font-bold px-2.5 py-1 rounded-full ${ROLE_COLOR[u.role] || ROLE_COLOR.VIEWER}`}>{u.role}</span>
              <MoreVertical size={15} className="text-textfaint" />
            </div>
          ))}
        </Card>
      </div>

      {showModal && <InviteModal onClose={() => setShowModal(false)} onSaved={() => { setShowModal(false); load(); }} />}
    </AppShell>
  );
}

function InviteModal({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState("VIEWER");
  const [password, setPassword] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.inviteUser({ email, full_name: fullName, role, password });
      onSaved();
    } catch (err: any) {
      setError(err.message || "Не удалось пригласить пользователя");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/65 flex items-center justify-center z-50">
      <div className="bg-card border border-border rounded-xl w-[400px] p-5">
        <div className="flex justify-between items-center mb-4">
          <span className="text-[15.5px] font-semibold text-white">Пригласить пользователя</span>
          <button onClick={onClose} className="text-textfaint"><X size={16} /></button>
        </div>
        <form onSubmit={handleSave} className="flex flex-col gap-3">
          <input className={inputClass} placeholder="Полное имя" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
          <input className={inputClass} type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <input className={inputClass} type="password" placeholder="Временный пароль" value={password} onChange={(e) => setPassword(e.target.value)} required />
          <select className={inputClass} value={role} onChange={(e) => setRole(e.target.value)}>
            <option value="VIEWER">VIEWER</option>
            <option value="ANALYST">ANALYST</option>
            <option value="MANAGER">MANAGER</option>
            <option value="ADMIN">ADMIN</option>
            <option value="OWNER">OWNER</option>
          </select>
          {error && <div className="text-red text-xs">{error}</div>}
          <div className="flex gap-2.5 mt-1">
            <button type="button" onClick={onClose} className="flex-1 border border-border text-textmuted rounded-lg py-2.5 text-[13px]">Отмена</button>
            <button type="submit" disabled={saving} className="flex-1 bg-accent text-white rounded-lg py-2.5 text-[13px] font-semibold disabled:opacity-60">
              {saving ? "Сохранение..." : "Пригласить"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
