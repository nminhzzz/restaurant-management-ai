"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { ApiError, apiFetch } from "@/lib/api-client";
import { saveSession } from "@/lib/session";

interface TokenRes {
  access_token: string;
  role: string;
  username: string;
}

export function LoginForm() {
  const router = useRouter();
  const [user, setUser] = useState("");
  const [pass, setPass] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setMsg(null);
    setLoading(true);
    try {
      const data = await apiFetch<TokenRes>("/settings/auth/login", {
        method: "POST",
        body: { username: user, password: pass },
      });
      saveSession({ token: data.access_token, role: data.role, username: data.username });
      setMsg("Đăng nhập thành công");
      router.push("/");
    } catch (e2) {
      if (e2 instanceof ApiError) setErr(e2.message);
      else setErr("Yêu cầu không thực hiện được.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div>
        <label htmlFor="login-user" className="block text-sm font-medium">Tên đăng nhập</label>
        <input id="login-user" value={user} onChange={(e) => setUser(e.target.value)} className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:ring-amber-500" />
      </div>
      <div>
        <label htmlFor="login-pass" className="block text-sm font-medium">Mật khẩu</label>
        <input id="login-pass" type="password" value={pass} onChange={(e) => setPass(e.target.value)} className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:ring-amber-500" />
      </div>
      {err && <p className="text-sm text-red-600">{err}</p>}
      {msg && <p className="text-sm text-emerald-600">{msg}</p>}
      <button type="submit" disabled={loading} className="w-full rounded-md bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700 disabled:opacity-50">
        {loading ? "Đang xử lý..." : "Đăng nhập"}
      </button>
    </form>
  );
}
