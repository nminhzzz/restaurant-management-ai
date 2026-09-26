import { roleLabel } from "@/lib/roles";

import { suggestionsFor } from "./suggestions";

export function Welcome({
  username,
  role,
  onAsk,
  composer,
}: {
  username: string | undefined;
  role: string | undefined;
  onAsk: (text: string) => void;
  composer: React.ReactNode;
}) {
  return (
    <div className="mx-auto grid w-full max-w-3xl gap-5 px-5 pt-16 pb-5 max-sm:pt-8">
      <div className="grid gap-2">
        <h2 className="text-3xl leading-[38px] font-bold tracking-tight text-balance">
          Chào {username ?? "bạn"}, hôm nay bạn muốn xem số liệu gì?
        </h2>
        <p className="text-[15px] text-muted">
          Hỏi bằng tiếng Việt về doanh thu, order, món bán chạy hay tồn kho. Trợ
          lý chỉ đọc dữ liệu trong phạm vi vai trò{" "}
          {role ? roleLabel(role) : "của bạn"}.
        </p>
      </div>
      {composer}
      <div className="grid gap-2 sm:grid-cols-2">
        {suggestionsFor(role)
          .slice(0, 4)
          .map((s) => (
            <button
              key={s.text}
              type="button"
              onClick={() => onAsk(s.text)}
              className="grid gap-1.5 rounded-container border border-border bg-surface px-3.5 py-3 text-left hover:border-ink hover:shadow-lift"
            >
              <span className="text-[11px] font-bold tracking-wider text-subtle uppercase">
                {s.topic}
              </span>
              <span className="text-[14.5px] font-semibold">{s.text}</span>
            </button>
          ))}
      </div>
    </div>
  );
}
