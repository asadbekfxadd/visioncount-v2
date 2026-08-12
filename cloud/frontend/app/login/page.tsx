"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Eye, AlertCircle } from "lucide-react";
import { api, setSession } from "@/lib/api";
import { inputClass } from "@/components/ui";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("owner@visioncount.uz");
  const [password, setPassword] = useState("demo1234");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await api.login(email, password);
      setSession(res.access_token, res.user);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Не удалось войти");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="h-screen w-full bg-bg flex items-center justify-center text-white">
      <div className="w-[380px]">
        <div className="flex items-center gap-2.5 justify-center mb-1.5">
          <div className="w-9 h-9 rounded-lg bg-accent flex items-center justify-center">
            <Eye size={19} color="#fff" />
          </div>
          <span className="text-2xl font-bold tracking-tight">VisionCount</span>
        </div>
        <p className="text-center text-textfaint text-[13px] mb-8">Understand every visitor.</p>

        <form onSubmit={handleSubmit} className="bg-card border border-border rounded-xl p-6 flex flex-col gap-4">
          <div>
            <label className="text-xs text-textmuted mb-1.5 block">Email</label>
            <input className={inputClass} type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div>
            <label className="text-xs text-textmuted mb-1.5 block">Пароль</label>
            <input className={inputClass} type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>

          {error && (
            <div className="flex items-center gap-2 text-red text-xs bg-red/10 border border-red/30 rounded-lg px-3 py-2">
              <AlertCircle size={14} /> {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="bg-accent text-white rounded-lg py-2.5 text-[13.5px] font-semibold disabled:opacity-60"
          >
            {loading ? "Вход..." : "Войти"}
          </button>

          <p className="text-[11.5px] text-textfaint text-center mt-1">
            Демо-доступ: owner@visioncount.uz / demo1234
          </p>
        </form>
      </div>
    </div>
  );
}
