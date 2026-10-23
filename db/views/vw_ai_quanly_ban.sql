-- Topic view; only the explicit projected columns are exposed.
CREATE OR REPLACE VIEW vw_ai_quanly_ban AS
SELECT MaBan, TenBan, TrangThai, SoChoNgoi FROM BAN WHERE DaXoa=0;
