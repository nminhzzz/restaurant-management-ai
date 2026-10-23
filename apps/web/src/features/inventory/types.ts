export type IngredientOption = {
  MaNguyenLieu: number;
  TenNguyenLieu: string;
  DonViTinh: string;
};

export type SupplierOption = {
  MaNhaCungCap: number;
  TenNhaCungCap: string;
};

export type Receipt = {
  MaPhieuNhap: number;
  MaNhaCungCap: number | null;
  NgayNhap: string | null;
  TrangThai: string;
};

export type StockIssue = {
  MaPhieuXuat: number;
  LyDo: string;
  TrangThai: string;
  NgayTao?: string | null;
  NguoiLap?: number | null;
  MaPhieuKiemKe?: number | null;
  GhiChu?: string | null;
  TongSoLuong?: number;
  SoDong?: number;
};

export type Stocktake = {
  MaPhieuKiemKe: number;
  TrangThai: string;
};

export const ISSUE_REASONS = ["Hao hụt", "Hết hạn", "Hỏng", "Khác"] as const;
