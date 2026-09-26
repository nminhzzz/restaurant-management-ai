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
