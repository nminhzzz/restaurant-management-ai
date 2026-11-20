import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { IssueDetailDialog } from "./issue-detail-dialog";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

const base = {
  MaPhieuXuat: 5,
  LyDo: "Hết hạn",
  TrangThai: "Chờ duyệt",
  NgayTao: "2026-11-19T06:00:00",
  Nguon: "Nguyên liệu",
  MaPhieuKiemKe: null,
  GhiChu: "Hệ thống đề xuất hủy các lô đã quá hạn sử dụng.",
  NguoiLap: null,
  TenNguoiLap: null,
  NguoiDuyet: null,
  TenNguoiDuyet: null,
  NgayDuyet: null,
  lines: [
    {
      MaChiTietXuat: 9,
      TenNguyenLieu: "Thịt bò",
      DonViTinh: "kg",
      SoLuong: 4,
      GiaVonUocTinh: null,
      MaLoNguyenLieu: 12,
      HanSuDung: "2026-11-17",
      MaChiTietOrder: null,
      SoSuat: null,
    },
  ],
};

describe("IssueDetailDialog", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("names the system as the author and shows each line's lot with its expiry", async () => {
    fetchMock.mockResolvedValue(base);
    render(<IssueDetailDialog issueId={5} onClose={() => {}} />);

    expect(await screen.findByText("Người lập")).toBeInTheDocument();
    expect(screen.getByText("Hệ thống")).toBeInTheDocument();
    expect(screen.getByText("#12 · HSD 17/11/2026")).toBeInTheDocument();
    expect(screen.queryByText("Người duyệt")).not.toBeInTheDocument();
  });

  it("shows who decided and when once the voucher was approved", async () => {
    fetchMock.mockResolvedValue({
      ...base,
      TrangThai: "Đã xác nhận",
      NguoiDuyet: 3,
      TenNguoiDuyet: "Bếp trưởng",
      NgayDuyet: "2026-11-19T09:30:00",
    });
    render(<IssueDetailDialog issueId={5} onClose={() => {}} />);

    expect(await screen.findByText("Người duyệt")).toBeInTheDocument();
    expect(screen.getByText("Bếp trưởng")).toBeInTheDocument();
    expect(screen.getByText("Thời điểm duyệt")).toBeInTheDocument();
    expect(
      screen.getByText("Thời điểm duyệt").nextElementSibling,
    ).toHaveTextContent(/09:30.*19\/11\/2026/);
  });

  it("names the staff member who wrote a manual voucher, and tolerates a lot-less line", async () => {
    fetchMock.mockResolvedValue({
      ...base,
      NguoiLap: 2,
      TenNguoiLap: "Thu ngân A",
      TrangThai: "Đã xác nhận",
      lines: [{ ...base.lines[0], MaLoNguyenLieu: null, HanSuDung: null }],
    });
    render(<IssueDetailDialog issueId={5} onClose={() => {}} />);

    expect(await screen.findByText("Thịt bò (kg)")).toBeInTheDocument();
    expect(screen.getByText("Người lập").nextElementSibling).toHaveTextContent(
      "Thu ngân A",
    );
    expect(screen.queryByText("Hệ thống")).not.toBeInTheDocument();
  });
});
