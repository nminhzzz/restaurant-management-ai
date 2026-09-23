-- vw_ai_quanly: full scope for MANAGER (all non-sensitive tables, no GiaVonUocTinh exposure control here - view excludes that column)
CREATE OR REPLACE VIEW vw_ai_quanly AS
SELECT MaOrder, BusinessDate, LoaiDon, TrangThai AS TrangThaiOrder, MaBan FROM `ORDER`;
