export type Dish = {
  MaMon: number;
  TenMon: string;
  TrangThai: string;
  TamDungThuCong?: boolean;
  MaNhomMon?: number | null;
  GiaHienTai?: number | null;
  HinhAnh?: string | null;
};

export type Group = { MaNhomMon: number; TenNhom: string };

export type Ingredient = {
  MaNguyenLieu: number;
  TenNguyenLieu: string;
  DonViTinh: string;
  MucTonToiThieu?: number | null;
  SoNgayBaoQuan?: number | null;
};

export type Supplier = {
  MaNhaCungCap: number;
  TenNhaCungCap: string;
  SoDienThoai?: string | null;
  Email?: string | null;
  NguoiLienHe?: string | null;
  DiaChi?: string | null;
  PhieuNhap?: { MaPhieuNhap: number }[];
};

export type DiningTable = {
  MaBan: number;
  TenBan: string;
  TrangThai?: string;
  KhuVuc?: string | null;
  SoChoNgoi?: number | null;
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
