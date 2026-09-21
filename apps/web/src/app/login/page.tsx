export default function LoginPage() {
  return (
    <main className="mx-auto w-full max-w-sm space-y-4 p-10">
      <h1 className="text-2xl font-semibold">Đăng nhập</h1>
      <p className="rounded-lg border border-dashed border-slate-300 bg-white p-4 text-sm text-slate-500">
        Biểu mẫu đăng nhập chưa được triển khai. Xác thực sẽ gọi
        <code className="mx-1 rounded bg-slate-100 px-1">
          POST /api/v1/auth/login
        </code>
        và lưu access token (FR-SET-02).
      </p>
    </main>
  );
}
