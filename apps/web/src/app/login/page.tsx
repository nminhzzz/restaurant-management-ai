import { LoginForm } from "@/features/auth/login-form";

export default function LoginPage() {
  return (
    <main className="mx-auto w-full max-w-sm space-y-4 p-10">
      <h1 className="text-2xl font-semibold">Đăng nhập</h1>
      <LoginForm />
    </main>
  );
}
