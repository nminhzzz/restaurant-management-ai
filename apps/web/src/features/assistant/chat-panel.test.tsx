import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { ChartView } from "./chart-view";
import { ChatPanel } from "./chat-panel";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

function stubFetch(body: unknown): void {
  fetchMock.mockResolvedValue(body);
}

const timeSeries = [
  { BusinessDate: "2026-09-01", DoanhThu: "100000" },
  { BusinessDate: "2026-09-02", DoanhThu: "120000" },
];

const shares = [
  { TenMon: "Phở bò", TyTrong: "60" },
  { TenMon: "Bún chả", TyTrong: "40" },
];

const chatResponseWithSql = {
  answer: "Doanh thu hôm qua là 1.000.000 đồng.",
  data: [{ DoanhThu: "1000000" }],
  chart: null,
  detail: {
    sql: "SELECT SUM(ThanhTien) AS DoanhThu FROM vw_ai_thungan",
    row_count: 1,
    view: "vw_ai_thungan",
    elapsed_ms: 12,
  },
};

const chatResponseWithScope = {
  answer:
    "Doanh thu hôm qua là 1.000.000 đồng.\n\nPhạm vi dữ liệu: vw_ai_thungan — đơn hàng, hóa đơn và thanh toán.",
  data: [{ DoanhThu: "1000000" }],
  chart: null,
  detail: null,
};

function ask(): void {
  fireEvent.change(screen.getByLabelText("Câu hỏi bằng tiếng Việt"), {
    target: { value: "Doanh thu hôm qua?" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Gửi câu hỏi" }));
}

describe("ChartView", () => {
  it("renders a line chart for a time series", () => {
    render(
      <ChartView
        spec={{ type: "line", x: "BusinessDate", y: ["DoanhThu"] }}
        rows={timeSeries}
      />,
    );

    expect(
      screen.getByRole("img", { name: /biểu đồ đường/i }),
    ).toBeInTheDocument();
  });

  it("renders a doughnut chart for shares", () => {
    render(
      <ChartView
        spec={{ type: "doughnut", x: "TenMon", y: ["TyTrong"] }}
        rows={shares}
      />,
    );

    expect(
      screen.getByRole("img", { name: /biểu đồ tròn/i }),
    ).toBeInTheDocument();
  });

  it("renders no chart when the server sends none", () => {
    const { container } = render(<ChartView spec={null} rows={timeSeries} />);

    expect(container).toBeEmptyDOMElement();
  });
});

describe("ChatPanel", () => {
  beforeEach(() => vi.resetAllMocks());

  it("renders the answer, the result rows and the query detail", async () => {
    stubFetch(chatResponseWithSql);

    render(<ChatPanel />);
    ask();

    expect(
      await screen.findByText(chatResponseWithSql.answer),
    ).toBeInTheDocument();
    expect(screen.getByRole("cell", { name: "1000000" })).toBeInTheDocument();
    expect(screen.getByText("vw_ai_thungan")).toBeInTheDocument();
  });

  // FR-AI-08
  it("keeps the SQL detail collapsed by default", async () => {
    stubFetch(chatResponseWithSql);

    render(<ChatPanel />);
    ask();

    const detail = await screen.findByText("Câu SQL đã chạy");
    expect(detail.closest("details")).not.toHaveAttribute("open");
  });

  // FR-AI-07 and business rule 16
  it("always shows the scope note next to the answer", async () => {
    stubFetch(chatResponseWithScope);

    render(<ChatPanel />);
    ask();

    expect(await screen.findByText(/vw_ai_thungan/)).toBeInTheDocument();
  });
});
