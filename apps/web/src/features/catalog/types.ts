export type Dish = {
  MaMon: number;
  TenMon: string;
  TrangThai: string;
  MaNhomMon?: number | null;
  GiaHienTai?: number | null;
  HinhAnh?: string | null;
  /** Manager's manual pause (FR-CAT-26); independent of the out-of-stock state. */
  TamDungThuCong?: boolean;
  /** Every reason that blocks ordering this dish. */
  LyDoChan?: string[];
};

export type Group = { MaNhomMon: number; TenNhom: string };

export type Ingredient = {
  MaNguyenLieu: number;
  TenNguyenLieu: string;
  DonViTinh: string;
  /** `null` means the ingredient follows the system default threshold. */
  MucTonToiThieu?: number | null;
  MucTonToiThieuApDung?: number | null;
};

export type Supplier = {
  MaNhaCungCap: number;
  TenNhaCungCap: string;
  SoDienThoai?: string | null;
  NguoiLienHe?: string | null;
  Email?: string | null;
  DiaChi?: string | null;
  PhieuNhap?: { MaPhieuNhap: number }[];
};

export type DiningTable = {
  MaBan: number;
  TenBan: string;
  TrangThai?: string;
  SoChoNgoi?: number | null;
  MaOrderDangPhucVu?: number | null;
};

export type RecipeItem = { MaNguyenLieu: number; SoLuong: number };

export type PriceVersion = {
  MaLichSuGia: number;
  MaMon: number;
  Gia: number;
  BusinessDateApDung: string;
  TrangThai: string;
  LoaiThayDoi: string;
};

export type RecipeVersionLine = {
  MaNguyenLieu: number;
  TenNguyenLieu: string;
  SoLuong: number;
  DonViTinh: string;
};

export type RecipeVersion = {
  MaCongThuc: number;
  MaMon: number;
  BusinessDateApDung: string;
  TrangThai: string;
  LoaiThayDoi: string;
  items: RecipeVersionLine[];
};
