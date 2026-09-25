"use client";

import { CircleAlert } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, apiFetch } from "@/lib/api-client";
import { homePathFor } from "@/lib/modules";
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
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setLoading(true);
    try {
      const data = await apiFetch<TokenRes>("/settings/auth/login", {
        method: "POST",
        body: { username: user, password: pass },
      });
      saveSession({
        token: data.access_token,
        role: data.role,
        username: data.username,
      });
      router.push(homePathFor(data.role));
    } catch (e2) {
      if (e2 instanceof ApiError) setErr(e2.message);
      else setErr("Không kết nối được máy chủ. Kiểm tra mạng rồi thử lại.");
      setLoading(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="login-user">Tên đăng nhập</Label>
        <Input
          id="login-user"
          autoComplete="username"
          className="h-11"
          value={user}
          onChange={(e) => setUser(e.target.value)}
          required
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="login-pass">Mật khẩu</Label>
        <Input
          id="login-pass"
          type="password"
          autoComplete="current-password"
          className="h-11"
          value={pass}
          onChange={(e) => setPass(e.target.value)}
          required
        />
      </div>
      {err && (
        <p role="alert" className="flex items-start gap-1.5 text-danger-fg">
          <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
          {err}
        </p>
      )}
      <Button type="submit" size="pos" className="w-full" disabled={loading}>
        {loading ? "Đang đăng nhập…" : "Đăng nhập"}
      </Button>
    </form>
  );
}
