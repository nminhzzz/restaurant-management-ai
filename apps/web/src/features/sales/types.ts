export type SalesStep = "floor" | "order" | "pay" | "done";

export type FloorOrder = {
  MaOrder: number;
  MaOrderHienThi: string | null;
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
