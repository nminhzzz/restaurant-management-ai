export type SalesStep = "floor" | "order" | "pay" | "done";

export type FloorOrder = {
  MaOrder: number;
  MaOrderHienThi: string | null;
  TrangThai?: string;
  MoLuc: string | null;
  SoMon: number;
  TamTinh: number;
};

export type FloorTable = {
  MaBan: number;
  TenBan: string;
  TrangThai: string;
  order: FloorOrder | null;
};

export type FloorBoard = { tables: FloorTable[]; takeaway: FloorOrder[] };

export type SelectionHold = {
  MaGiuCho: number;
  MaLuotChon: string;
  MaMon: number;
  SoLuong: number;
  ThoiDiemHetHan: string;
  TrangThai: string;
};

export type SelectionSubmit = {
  MaOrder: number | null;
  MaOrderHienThi?: string | null;
  CanXacNhanLai: boolean;
  stale: { MaGiuCho: number; MaMon: number }[];
  lines: SentSelectionLine[];
};

export type SentSelectionLine = {
  MaChiTietOrder: number;
  MaMon: number;
  SoLuong: number;
  DonGia: number;
  TrangThai: string;
};

/** Orders whose money is settled or abandoned: the table is released by the cashier. */
export const FINISHED_ORDER_STATUSES = [
  "Đã thanh toán",
  "Đóng – chưa thu được tiền",
  "Đã hủy",
  "Tự động đóng",
];

export type PaymentException = {
  MaGiaoDich: number;
  MaOrder: number;
  MaOrderHienThi: string | null;
  TrangThaiOrder: string;
  TongTienOrder: number;
  SoTienNgoaiLe: number;
  MaGiaoDichCong: string | null;
  MaGiaoDichNganHang: string | null;
  TrangThaiNgoaiLe: string;
  MaThamChieuHoan: string | null;
  ThoiDiemNhan: string | null;
  ThoiDiemXuLy: string | null;
  NguoiXuLy: number | null;
  CoTheApDung: boolean;
};

export type ProvisionalBill = {
  TieuDe: string;
  TenNhaHang?: string | null;
  DiaChi?: string | null;
  MaOrderHienThi: string | null;
  LoaiDon?: string;
  TenBan?: string | null;
  TrangThai: string;
  ThoiDiemIn: string;
  TongTien: number;
  lines: {
    MaMon: number;
    TenMon: string;
    SoLuong: number;
    DonGia: number;
    ThanhTien: number;
    GhiChu: string | null;
  }[];
};
